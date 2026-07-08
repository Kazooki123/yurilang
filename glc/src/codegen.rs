//! # Yuri Code Generation
//! 
//! Lowers a Yuri [`Program`] to a native object file using Cranelift.
//!
//! `@ship` functions are monomorphized: since Yuri parameters aren't
//! type-annotated, each function is compiled once per distinct tuple of
//! argument types actually used at its call sites (memoized in
//! `World::specialized`), the same way C++ templates or Rust generics
//! work. Compiling a specialization runs a small type-only inference
//! pass first (`infer_ty`/`infer_block_ty`, no Cranelift calls) to
//! learn parameter/local/return types before a Cranelift function
//! signature can even be declared, then does the real IR-emitting pass
//! (`FnCodegen::compile_*`) against that now-known signature.
//!
//! `main` (the `@wlw` entry point) is compiled the same way as any
//! other function body, just with a fixed `() -> i32` signature instead
//! of an inferred one.
//!
//! Printing goes through a tiny fixed-arity C runtime (`runtime.c`,
//! compiled and linked in by `main.rs`) instead of calling variadic
//! libc functions (printf/sprintf) directly from generated IR -- see
//! that file for why.
//!
//! `NOTE for future readers hitting a Cranelift version mismatch`: the
//! spots most likely to need small signature tweaks across
//! cranelift-codegen/cranelift-frontend releases are `brif`/`jump`
//! (block-argument slice type has changed shape a couple of times) and
//! wherever `DataDescription`/`FuncId`/`Variable` are constructed
//! directly. The overall approach (declare data -> global_value,
//! Variable-based SSA construction for control flow) is stable; it's
//! just exact method/type names that drift.

use std::collections::{HashMap, HashSet};

use anyhow::{anyhow, bail, Result};
use cranelift_entity::EntityRef;
use cranelift_codegen::ir::condcodes::{FloatCC, IntCC};
use cranelift_codegen::ir::{types, AbiParam, FuncRef, InstBuilder, Signature, Value};
use cranelift_codegen::isa::CallConv;
use cranelift_codegen::settings::{self, Configurable};
use cranelift_frontend::{FunctionBuilder, FunctionBuilderContext, Variable};
use cranelift_module::{DataDescription, FuncId, Linkage, Module};
use cranelift_object::{ObjectBuilder, ObjectModule};

use crate::ast::{BinOp, CmpOp, Expr, Program, ShipDef, Stmt};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
enum Ty {
    Str,
    Int,
    Float,
}

fn ty_to_clif(ty: Ty, ptr_type: types::Type) -> types::Type {
    match ty {
        Ty::Str => ptr_type,
        Ty::Int => types::I64,
        Ty::Float => types::F64,
    }
}

#[derive(Clone, Copy)]
struct RuntimeIds {
    print_str: FuncId,
    print_int: FuncId,
    print_float: FuncId,
    print_space: FuncId,
    print_newline: FuncId,
}

/// Per-function-instance `FuncRef` handles for the print runtime --
/// computed fresh for each function body via `declare_func_in_func`,
/// since `FuncRef`s (unlike `FuncId`s) are only valid within the
/// function they were declared in.
struct Runtime {
    print_str: FuncRef,
    print_int: FuncRef,
    print_float: FuncRef,
    print_space: FuncRef,
    print_newline: FuncRef,
}

impl Runtime {
    fn declare_in(world: &mut World, builder: &mut FunctionBuilder) -> Runtime {
        Runtime {
            print_str: world
                .module
                .declare_func_in_func(world.runtime_ids.print_str, builder.func),
            print_int: world
                .module
                .declare_func_in_func(world.runtime_ids.print_int, builder.func),
            print_float: world
                .module
                .declare_func_in_func(world.runtime_ids.print_float, builder.func),
            print_space: world
                .module
                .declare_func_in_func(world.runtime_ids.print_space, builder.func),
            print_newline: world
                .module
                .declare_func_in_func(world.runtime_ids.print_newline, builder.func),
        }
    }
}

struct World {
    module: ObjectModule,
    call_conv: CallConv,
    ptr_type: types::Type,
    runtime_ids: RuntimeIds,
    functions: HashMap<String, ShipDef>,
    specialized: HashMap<(String, Vec<Ty>), (FuncId, Option<Ty>)>,
    in_progress: HashSet<(String, Vec<Ty>)>,
    string_counter: usize,
}

pub fn compile_to_object(program: &Program) -> Result<Vec<u8>> {
    let mut flag_builder = settings::builder();
    flag_builder
        .set("is_pic", "true")
        .map_err(|e| anyhow!("cranelift flag error: {e}"))?;
    let flags = settings::Flags::new(flag_builder);

    let isa_builder =
        cranelift_native::builder().map_err(|e| anyhow!("failed to detect host ISA: {e}"))?;
    let isa = isa_builder
        .finish(flags)
        .map_err(|e| anyhow!("failed to build target ISA: {e}"))?;
    let call_conv = isa.default_call_conv();

    let object_builder = ObjectBuilder::new(
        isa,
        "yuri_module",
        cranelift_module::default_libcall_names(),
    )
    .map_err(|e| anyhow!("failed to create object builder: {e}"))?;
    let mut module = ObjectModule::new(object_builder);

    let ptr_type = module.target_config().pointer_type();

    let runtime_ids = RuntimeIds {
        print_str: declare_extern(&mut module, "yuri_print_str", call_conv, &[ptr_type], &[])?,
        print_int: declare_extern(&mut module, "yuri_print_int", call_conv, &[types::I64], &[])?,
        print_float: declare_extern(
            &mut module,
            "yuri_print_float",
            call_conv,
            &[types::F64],
            &[],
        )?,
        print_space: declare_extern(&mut module, "yuri_print_space", call_conv, &[], &[])?,
        print_newline: declare_extern(&mut module, "yuri_print_newline", call_conv, &[], &[])?,
    };

    let functions: HashMap<String, ShipDef> = program
        .functions
        .iter()
        .cloned()
        .map(|f| (f.name.clone(), f))
        .collect();

    let mut world = World {
        module,
        call_conv,
        ptr_type,
        runtime_ids,
        functions,
        specialized: HashMap::new(),
        in_progress: HashSet::new(),
        string_counter: 0,
    };

    let mut main_sig = Signature::new(call_conv);
    main_sig.returns.push(AbiParam::new(types::I32));
    let main_id = world
        .module
        .declare_function("main", Linkage::Export, &main_sig)
        .map_err(|e| anyhow!("failed to declare main: {e}"))?;

    let mut clif_ctx = world.module.make_context();
    clif_ctx.func.signature = main_sig;
    let mut fn_builder_ctx = FunctionBuilderContext::new();
    {
        let mut builder = FunctionBuilder::new(&mut clif_ctx.func, &mut fn_builder_ctx);
        let entry_block = builder.create_block();
        builder.append_block_params_for_function_params(entry_block);
        builder.switch_to_block(entry_block);
        builder.seal_block(entry_block);

        let runtime = Runtime::declare_in(&mut world, &mut builder);

        {
            let mut fc = FnCodegen {
                world: &mut world,
                builder: &mut builder,
                runtime,
                env: HashMap::new(),
                next_var: 0,
                frozen: HashSet::new(),
                in_function: false,
                ret_ty: None,
            };
            fc.compile_block(&program.entry)?;
        }

        let zero = builder.ins().iconst(types::I32, 0);
        builder.ins().return_(&[zero]);
        builder.finalize();
    }

    world
        .module
        .define_function(main_id, &mut clif_ctx)
        .map_err(|e| anyhow!("failed to define main: {e}"))?;
    world.module.clear_context(&mut clif_ctx);

    let product = world.module.finish();
    product
        .emit()
        .map_err(|e| anyhow!("failed to emit object bytes: {e}"))
}

fn declare_extern(
    module: &mut ObjectModule,
    name: &str,
    call_conv: CallConv,
    params: &[types::Type],
    returns: &[types::Type],
) -> Result<FuncId> {
    let mut sig = Signature::new(call_conv);
    for &p in params {
        sig.params.push(AbiParam::new(p));
    }
    for &r in returns {
        sig.returns.push(AbiParam::new(r));
    }
    module
        .declare_function(name, Linkage::Import, &sig)
        .map_err(|e| anyhow!("failed to declare {name}: {e}"))
}

fn mangle(name: &str, arg_types: &[Ty]) -> String {
    let mut s = format!("__yuri_fn_{name}");
    for t in arg_types {
        s.push_str(match t {
            Ty::Str => "_s",
            Ty::Int => "_i",
            Ty::Float => "_f",
        });
    }
    s
}

/// Gets (compiling if necessary) the specialization of `name` for the
/// given argument types. Memoized in `world.specialized`; a
/// specialization currently mid-compile means indirect recursion, which
/// isn't supported yet.
fn ensure_specialized(
    world: &mut World,
    name: &str,
    arg_types: &[Ty],
) -> Result<(FuncId, Option<Ty>)> {
    let key = (name.to_string(), arg_types.to_vec());
    if let Some(&result) = world.specialized.get(&key) {
        return Ok(result);
    }
    if world.in_progress.contains(&key) {
        bail!(
            "`{name}` recurses (directly or indirectly) -- recursive @ship functions aren't supported yet"
        );
    }

    let def = world
        .functions
        .get(name)
        .cloned()
        .ok_or_else(|| anyhow!("call to undefined function: {name}"))?;
    if def.params.len() != arg_types.len() {
        bail!(
            "`{name}` expects {} argument(s), got {}",
            def.params.len(),
            arg_types.len()
        );
    }

    world.in_progress.insert(key.clone());

    let mut ty_env: HashMap<String, Ty> = def
        .params
        .iter()
        .cloned()
        .zip(arg_types.iter().copied())
        .collect();
    let ret_ty = infer_block_ty(world, &def.body, &mut ty_env)?;

    let mut sig = Signature::new(world.call_conv);
    for &t in arg_types {
        sig.params.push(AbiParam::new(ty_to_clif(t, world.ptr_type)));
    }
    if let Some(rt) = ret_ty {
        sig.returns.push(AbiParam::new(ty_to_clif(rt, world.ptr_type)));
    }

    let mangled = mangle(name, arg_types);
    let fid = world
        .module
        .declare_function(&mangled, Linkage::Local, &sig)
        .map_err(|e| anyhow!("failed to declare {name}: {e}"))?;

    world.specialized.insert(key.clone(), (fid, ret_ty));

    let mut clif_ctx = world.module.make_context();
    clif_ctx.func.signature = sig;
    let mut fn_builder_ctx = FunctionBuilderContext::new();
    {
        let mut builder = FunctionBuilder::new(&mut clif_ctx.func, &mut fn_builder_ctx);
        let entry_block = builder.create_block();
        builder.append_block_params_for_function_params(entry_block);
        builder.switch_to_block(entry_block);
        builder.seal_block(entry_block);
        let param_vals: Vec<Value> = builder.block_params(entry_block).to_vec();

        let runtime = Runtime::declare_in(world, &mut builder);

        {
            let mut fc = FnCodegen {
                world: &mut *world,
                builder: &mut builder,
                runtime,
                env: HashMap::new(),
                next_var: 0,
                frozen: HashSet::new(),
                in_function: true,
                ret_ty,
            };

            for (i, pname) in def.params.iter().enumerate() {
                let pty = arg_types[i];
                let var = fc.fresh_var(pty);
                fc.builder.def_var(var, param_vals[i]);
                fc.env.insert(pname.clone(), (var, pty));
            }

            let terminated = fc.compile_block(&def.body)?;
            if !terminated {
                if ret_ty.is_some() {
                    bail!("not every path through `{name}` reaches a @promise");
                }
                fc.builder.ins().return_(&[]);
            }
        }

        builder.finalize();
    }

    world
        .module
        .define_function(fid, &mut clif_ctx)
        .map_err(|e| anyhow!("failed to define {name}: {e}"))?;
    world.module.clear_context(&mut clif_ctx);

    world.in_progress.remove(&key);
    Ok((fid, ret_ty))
}

/// Pure type inference over a function body -- no Cranelift IR is
/// emitted here. Returns the type flowing out of any `@promise`
/// statements found (`None` if the function never promises anything,
/// i.e. it's void). Mutates `env` the same way real codegen mutates its
/// symbol table (flat/function-scoped, matching `FnCodegen`).
fn infer_block_ty(
    world: &mut World,
    stmts: &[Stmt],
    env: &mut HashMap<String, Ty>,
) -> Result<Option<Ty>> {
    let mut found: Option<Ty> = None;

    for stmt in stmts {
        match stmt {
            Stmt::Bond { name, value } => {
                let t = infer_ty(world, value, env)?;
                env.insert(name.clone(), t);
            }
            Stmt::Confess { values } => {
                for v in values {
                    infer_ty(world, v, env)?;
                }
            }
            Stmt::Awaken(_) => {}
            Stmt::Promise(e) => {
                let t = infer_ty(world, e, env)?;
                reconcile_return_ty(&mut found, t)?;
            }
            Stmt::If {
                cond,
                then_body,
                else_body,
            } => {
                infer_ty(world, cond, env)?;
                if let Some(t) = infer_block_ty(world, then_body, env)? {
                    reconcile_return_ty(&mut found, t)?;
                }
                if let Some(else_stmts) = else_body {
                    if let Some(t) = infer_block_ty(world, else_stmts, env)? {
                        reconcile_return_ty(&mut found, t)?;
                    }
                }
            }
            Stmt::Cling { count, body } => {
                infer_ty(world, count, env)?;
                if let Some(t) = infer_block_ty(world, body, env)? {
                    reconcile_return_ty(&mut found, t)?;
                }
            }
            Stmt::CallStmt { name, args } => {
                let arg_tys = args
                    .iter()
                    .map(|a| infer_ty(world, a, env))
                    .collect::<Result<Vec<_>>>()?;
                ensure_specialized(world, name, &arg_tys)?;
            }
        }
    }

    Ok(found)
}

fn reconcile_return_ty(found: &mut Option<Ty>, t: Ty) -> Result<()> {
    match found {
        None => *found = Some(t),
        Some(prev) if *prev == t => {}
        Some(prev) => bail!(
            "a function's @promise values disagree in type ({:?} vs {:?}) -- every path must return the same type",
            prev,
            t
        ),
    }
    Ok(())
}

fn infer_ty(world: &mut World, expr: &Expr, env: &HashMap<String, Ty>) -> Result<Ty> {
    match expr {
        Expr::Int(_) => Ok(Ty::Int),
        Expr::Float(_) => Ok(Ty::Float),
        Expr::Str(_) => Ok(Ty::Str),
        Expr::Var(name) => env
            .get(name)
            .copied()
            .ok_or_else(|| anyhow!("undeclared variable: {name}")),
        Expr::Bin(_, l, r) => {
            let lt = infer_ty(world, l, env)?;
            let rt = infer_ty(world, r, env)?;
            if lt == Ty::Str || rt == Ty::Str {
                bail!("`plus`/`minus`/`times`/`divide` don't work on strings yet");
            }
            Ok(if lt == Ty::Float || rt == Ty::Float {
                Ty::Float
            } else {
                Ty::Int
            })
        }
        Expr::Cmp(_, l, r) => {
            let lt = infer_ty(world, l, env)?;
            let rt = infer_ty(world, r, env)?;
            if lt == Ty::Str || rt == Ty::Str {
                bail!("comparing strings isn't supported yet");
            }
            Ok(Ty::Int) // booleans are plain 0/1 Ty::Int values
        }
        Expr::Call { name, args } => {
            let arg_tys = args
                .iter()
                .map(|a| infer_ty(world, a, env))
                .collect::<Result<Vec<_>>>()?;
            let (_, ret) = ensure_specialized(world, name, &arg_tys)?;
            ret.ok_or_else(|| {
                anyhow!(
                    "`{name}` doesn't return a value (no @promise), so it can't be used in an expression"
                )
            })
        }
    }
}

/// Per-function codegen state: the active builder, the whole-program
/// `World`, the symbol table, and handles to the print runtime.
struct FnCodegen<'a, 'b> {
    world: &'a mut World,
    builder: &'a mut FunctionBuilder<'b>,
    runtime: Runtime,
    env: HashMap<String, (Variable, Ty)>,
    next_var: u32,
    frozen: HashSet<String>,
    in_function: bool,
    ret_ty: Option<Ty>,
}

impl<'a, 'b> FnCodegen<'a, 'b> {
    fn fresh_var(&mut self, ty: Ty) -> Variable {
        let var = Variable::new(self.next_var as usize);
        self.next_var += 1;
        self.builder
            .declare_var(var, ty_to_clif(ty, self.world.ptr_type));
        var
    }

    fn zero_value(&mut self, ty: Ty) -> Value {
        match ty {
            Ty::Int => self.builder.ins().iconst(types::I64, 0),
            Ty::Float => self.builder.ins().f64const(0.0),
            Ty::Str => self.builder.ins().iconst(self.world.ptr_type, 0),
        }
    }

    fn intern_string(&mut self, s: &str) -> Result<Value> {
        let mut bytes = s.as_bytes().to_vec();
        bytes.push(0);
        let data_name = format!("__yuri_str_{}", self.world.string_counter);
        self.world.string_counter += 1;

        let data_id = self
            .world
            .module
            .declare_data(&data_name, Linkage::Local, false, false)
            .map_err(|e| anyhow!("failed to declare string data: {e}"))?;

        let mut desc = DataDescription::new();
        desc.define(bytes.into_boxed_slice());
        self.world
            .module
            .define_data(data_id, &desc)
            .map_err(|e| anyhow!("failed to define string data: {e}"))?;

        let gv = self
            .world
            .module
            .declare_data_in_func(data_id, self.builder.func);
        Ok(self.builder.ins().global_value(self.world.ptr_type, gv))
    }

    fn to_float(&mut self, v: Value, ty: Ty) -> Value {
        match ty {
            Ty::Float => v,
            Ty::Int => self.builder.ins().fcvt_from_sint(types::F64, v),
            Ty::Str => unreachable!("strings are rejected before to_float is called"),
        }
    }

    fn compile_expr(&mut self, expr: &Expr) -> Result<(Value, Ty)> {
        match expr {
            Expr::Int(n) => Ok((self.builder.ins().iconst(types::I64, *n), Ty::Int)),
            Expr::Float(f) => Ok((self.builder.ins().f64const(*f), Ty::Float)),
            Expr::Str(s) => Ok((self.intern_string(s)?, Ty::Str)),
            Expr::Var(name) => {
                let (var, ty) = *self
                    .env
                    .get(name)
                    .ok_or_else(|| anyhow!("undeclared variable: {name}"))?;
                Ok((self.builder.use_var(var), ty))
            }
            Expr::Bin(op, lhs, rhs) => self.compile_bin(*op, lhs, rhs),
            Expr::Cmp(op, lhs, rhs) => self.compile_cmp(*op, lhs, rhs),
            Expr::Call { name, args } => self.compile_call(name, args),
        }
    }

    fn compile_call(&mut self, name: &str, args: &[Expr]) -> Result<(Value, Ty)> {
        let mut arg_vals = Vec::with_capacity(args.len());
        let mut arg_tys = Vec::with_capacity(args.len());
        for a in args {
            let (v, t) = self.compile_expr(a)?;
            arg_vals.push(v);
            arg_tys.push(t);
        }

        let (fid, ret_ty) = ensure_specialized(self.world, name, &arg_tys)?;
        let ret_ty = ret_ty.ok_or_else(|| {
            anyhow!(
                "`{name}` doesn't return a value (no @promise), so it can't be used in an expression"
            )
        })?;

        let func_ref = self
            .world
            .module
            .declare_func_in_func(fid, self.builder.func);
        let call = self.builder.ins().call(func_ref, &arg_vals);
        let result = self.builder.inst_results(call)[0];
        Ok((result, ret_ty))
    }

    fn compile_bin(&mut self, op: BinOp, lhs: &Expr, rhs: &Expr) -> Result<(Value, Ty)> {
        let (lv, lty) = self.compile_expr(lhs)?;
        let (rv, rty) = self.compile_expr(rhs)?;

        if lty == Ty::Str || rty == Ty::Str {
            bail!("`plus`/`minus`/`times`/`divide` don't work on strings yet");
        }

        if lty == Ty::Int && rty == Ty::Int {
            let v = match op {
                BinOp::Add => self.builder.ins().iadd(lv, rv),
                BinOp::Sub => self.builder.ins().isub(lv, rv),
                BinOp::Mul => self.builder.ins().imul(lv, rv),
                BinOp::Div => self.builder.ins().sdiv(lv, rv),
            };
            Ok((v, Ty::Int))
        } else {
            let lv = self.to_float(lv, lty);
            let rv = self.to_float(rv, rty);
            let v = match op {
                BinOp::Add => self.builder.ins().fadd(lv, rv),
                BinOp::Sub => self.builder.ins().fsub(lv, rv),
                BinOp::Mul => self.builder.ins().fmul(lv, rv),
                BinOp::Div => self.builder.ins().fdiv(lv, rv),
            };
            Ok((v, Ty::Float))
        }
    }

    fn compile_cmp(&mut self, op: CmpOp, lhs: &Expr, rhs: &Expr) -> Result<(Value, Ty)> {
        let (lv, lty) = self.compile_expr(lhs)?;
        let (rv, rty) = self.compile_expr(rhs)?;

        if lty == Ty::Str || rty == Ty::Str {
            bail!("comparing strings isn't supported yet");
        }

        let v = if lty == Ty::Int && rty == Ty::Int {
            let cc = match op {
                CmpOp::Gt => IntCC::SignedGreaterThan,
                CmpOp::Lt => IntCC::SignedLessThan,
                CmpOp::Ge => IntCC::SignedGreaterThanOrEqual,
                CmpOp::Le => IntCC::SignedLessThanOrEqual,
                CmpOp::Eq => IntCC::Equal,
                CmpOp::Ne => IntCC::NotEqual,
            };
            self.builder.ins().icmp(cc, lv, rv)
        } else {
            let lv = self.to_float(lv, lty);
            let rv = self.to_float(rv, rty);
            let cc = match op {
                CmpOp::Gt => FloatCC::GreaterThan,
                CmpOp::Lt => FloatCC::LessThan,
                CmpOp::Ge => FloatCC::GreaterThanOrEqual,
                CmpOp::Le => FloatCC::LessThanOrEqual,
                CmpOp::Eq => FloatCC::Equal,
                CmpOp::Ne => FloatCC::NotEqual,
            };
            self.builder.ins().fcmp(cc, lv, rv)
        };

        Ok((v, Ty::Int))
    }

    fn emit_print(&mut self, val: Value, ty: Ty) {
        let func_ref = match ty {
            Ty::Str => self.runtime.print_str,
            Ty::Int => self.runtime.print_int,
            Ty::Float => self.runtime.print_float,
        };
        self.builder.ins().call(func_ref, &[val]);
    }

    fn compile_block(&mut self, stmts: &[Stmt]) -> Result<bool> {
        for stmt in stmts {
            if self.compile_stmt(stmt)? {
                return Ok(true);
            }
        }
        Ok(false)
    }

    fn compile_stmt(&mut self, stmt: &Stmt) -> Result<bool> {
        match stmt {
            Stmt::Bond { name, value } => {
                if self.frozen.contains(name) {
                    bail!(
                        "Yuri error: `{name}` has awakened and knows herself now - she can't be @bond-ed again."
                    );
                }
                let (val, ty) = self.compile_expr(value)?;
                let var = self.fresh_var(ty);
                self.builder.def_var(var, val);
                self.env.insert(name.clone(), (var, ty));
                Ok(false)
            }

            Stmt::Confess { values } => {
                for (i, expr) in values.iter().enumerate() {
                    if i > 0 {
                        self.builder.ins().call(self.runtime.print_space, &[]);
                    }
                    let (val, ty) = self.compile_expr(expr)?;
                    self.emit_print(val, ty);
                }
                self.builder.ins().call(self.runtime.print_newline, &[]);
                Ok(false)
            }

            Stmt::Awaken(name) => {
                if !self.env.contains_key(name) {
                    bail!("can't @awaken `{name}`: it was never @bond-ed");
                }
                self.frozen.insert(name.clone());
                Ok(false)
            }

            Stmt::Promise(expr) => {
                if !self.in_function {
                    bail!("@promise can only be used inside a @ship function");
                }
                let (val, _ty) = self.compile_expr(expr)?;
                self.builder.ins().return_(&[val]);
                Ok(true)
            }

            Stmt::CallStmt { name, args } => {
                let mut arg_vals = Vec::with_capacity(args.len());
                let mut arg_tys = Vec::with_capacity(args.len());
                for a in args {
                    let (v, t) = self.compile_expr(a)?;
                    arg_vals.push(v);
                    arg_tys.push(t);
                }
                let (fid, _ret_ty) = ensure_specialized(self.world, name, &arg_tys)?;
                let func_ref = self
                    .world
                    .module
                    .declare_func_in_func(fid, self.builder.func);
                self.builder.ins().call(func_ref, &arg_vals);
                Ok(false)
            }

            Stmt::If {
                cond,
                then_body,
                else_body,
            } => {
                let (cond_val, cond_ty) = self.compile_expr(cond)?;
                if cond_ty != Ty::Int {
                    bail!("@jealous needs a comparison or integer condition");
                }

                let then_block = self.builder.create_block();
                let else_block = self.builder.create_block();
                let merge_block = self.builder.create_block();

                self.builder
                    .ins()
                    .brif(cond_val, then_block, &[], else_block, &[]);

                self.builder.switch_to_block(then_block);
                self.builder.seal_block(then_block);
                let then_terminated = self.compile_block(then_body)?;
                if !then_terminated {
                    self.builder.ins().jump(merge_block, &[]);
                }

                self.builder.switch_to_block(else_block);
                self.builder.seal_block(else_block);
                let else_terminated = match else_body {
                    Some(else_stmts) => self.compile_block(else_stmts)?,
                    None => false,
                };
                if !else_terminated {
                    self.builder.ins().jump(merge_block, &[]);
                }

                self.builder.switch_to_block(merge_block);
                self.builder.seal_block(merge_block);

                if then_terminated && else_terminated {
                    match self.ret_ty {
                        Some(t) => {
                            let dummy = self.zero_value(t);
                            self.builder.ins().return_(&[dummy]);
                        }
                        None => {
                            self.builder.ins().return_(&[]);
                        }
                    }
                    Ok(true)
                } else {
                    Ok(false)
                }
            }

            Stmt::Cling { count, body } => {
                let (count_val, count_ty) = self.compile_expr(count)?;
                if count_ty != Ty::Int {
                    bail!("@cling's repeat count must be an integer");
                }

                let i_var = self.fresh_var(Ty::Int);
                let zero = self.builder.ins().iconst(types::I64, 0);
                self.builder.def_var(i_var, zero);

                let loop_head = self.builder.create_block();
                let loop_body = self.builder.create_block();
                let loop_exit = self.builder.create_block();

                self.builder.ins().jump(loop_head, &[]);

                self.builder.switch_to_block(loop_head);
                let i_val = self.builder.use_var(i_var);
                let keep_going = self
                    .builder
                    .ins()
                    .icmp(IntCC::SignedLessThan, i_val, count_val);
                self.builder
                    .ins()
                    .brif(keep_going, loop_body, &[], loop_exit, &[]);

                self.builder.switch_to_block(loop_body);
                self.builder.seal_block(loop_body);
                let body_terminated = self.compile_block(body)?;
                if body_terminated {
                    bail!("@promise inside a @cling loop isn't supported yet");
                }

                let i_val2 = self.builder.use_var(i_var);
                let one = self.builder.ins().iconst(types::I64, 1);
                let next_i = self.builder.ins().iadd(i_val2, one);
                self.builder.def_var(i_var, next_i);
                self.builder.ins().jump(loop_head, &[]);

                self.builder.seal_block(loop_head);

                self.builder.switch_to_block(loop_exit);
                self.builder.seal_block(loop_exit);
                Ok(false)
            }
        }
    }
}
