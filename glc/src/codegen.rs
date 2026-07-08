//! Lowers a Yuri [`Program`] to a native object file using Cranelift.
//!
//! Everything still lives in one function, `main` -- `@jealous`/`@forgive`
//! and `@cling` lower to more Cranelift blocks and branches inside it,
//! not to separate functions. Variables are function-scoped (no block
//! scoping): a `@bond` inside an if-body is visible after it too, same
//! as the Python interpreter.
//!
//! Printing goes through a tiny fixed-arity C runtime (`runtime.c`,
//! compiled and linked in by `main.rs`) instead of calling variadic
//! libc functions (printf/sprintf) directly from generated IR -- see
//! that file for why.
//!
//! NOTE for future readers hitting a Cranelift version mismatch: the
//! spots most likely to need small signature tweaks across
//! cranelift-codegen/cranelift-frontend releases are `brif`/`jump`
//! (block-argument slice type has changed shape a couple of times) and
//! wherever `DataDescription`/`FuncId`/`Variable` are constructed
//! directly. The overall approach (declare data -> global_value,
//! Variable-based SSA construction for control flow) is stable; it's
//! just the exact method/type names that drift.

use std::collections::HashMap;

use anyhow::{anyhow, bail, Result};
use cranelift_entity::EntityRef;
use cranelift_codegen::ir::condcodes::{FloatCC, IntCC};
use cranelift_codegen::ir::{types, AbiParam, FuncRef, InstBuilder, Signature, Value};
use cranelift_codegen::isa::CallConv;
use cranelift_codegen::settings::{self, Configurable};
use cranelift_frontend::{FunctionBuilder, FunctionBuilderContext, Variable};
use cranelift_module::{DataDescription, FuncId, Linkage, Module};
use cranelift_object::{ObjectBuilder, ObjectModule};

use crate::ast::{BinOp, CmpOp, Expr, Program, Stmt};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
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

struct Runtime {
    print_str: FuncRef,
    print_int: FuncRef,
    print_float: FuncRef,
    print_space: FuncRef,
    print_newline: FuncRef,
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

    let print_str_id = declare_extern(&mut module, "yuri_print_str", call_conv, &[ptr_type], &[])?;
    let print_int_id =
        declare_extern(&mut module, "yuri_print_int", call_conv, &[types::I64], &[])?;
    let print_float_id =
        declare_extern(&mut module, "yuri_print_float", call_conv, &[types::F64], &[])?;
    let print_space_id = declare_extern(&mut module, "yuri_print_space", call_conv, &[], &[])?;
    let print_newline_id =
        declare_extern(&mut module, "yuri_print_newline", call_conv, &[], &[])?;

    let mut main_sig = Signature::new(call_conv);
    main_sig.returns.push(AbiParam::new(types::I32));
    let main_id = module
        .declare_function("main", Linkage::Export, &main_sig)
        .map_err(|e| anyhow!("failed to declare main: {e}"))?;

    let mut ctx = module.make_context();
    ctx.func.signature = main_sig;

    let mut fn_builder_ctx = FunctionBuilderContext::new();
    {
        let mut builder = FunctionBuilder::new(&mut ctx.func, &mut fn_builder_ctx);
        let entry_block = builder.create_block();
        builder.append_block_params_for_function_params(entry_block);
        builder.switch_to_block(entry_block);
        builder.seal_block(entry_block);

        let runtime = Runtime {
            print_str: module.declare_func_in_func(print_str_id, builder.func),
            print_int: module.declare_func_in_func(print_int_id, builder.func),
            print_float: module.declare_func_in_func(print_float_id, builder.func),
            print_space: module.declare_func_in_func(print_space_id, builder.func),
            print_newline: module.declare_func_in_func(print_newline_id, builder.func),
        };

        {
            let mut fc = FnCodegen {
                builder: &mut builder,
                module: &mut module,
                ptr_type,
                runtime: &runtime,
                env: HashMap::new(),
                next_var: 0,
                string_counter: 0,
            };

            for stmt in &program.entry {
                fc.compile_stmt(stmt)?;
            }
        }

        let zero = builder.ins().iconst(types::I32, 0);
        builder.ins().return_(&[zero]);
        builder.finalize();
    }

    module
        .define_function(main_id, &mut ctx)
        .map_err(|e| anyhow!("failed to define main: {e}"))?;
    module.clear_context(&mut ctx);

    let product = module.finish();
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

/// Per-function codegen state: the active builder, the module (for
/// interning string constants), the symbol table, and handles to the
/// print runtime.
struct FnCodegen<'a, 'b> {
    builder: &'a mut FunctionBuilder<'b>,
    module: &'a mut ObjectModule,
    ptr_type: types::Type,
    runtime: &'a Runtime,
    env: HashMap<String, (Variable, Ty)>,
    next_var: u32,
    string_counter: usize,
}

impl<'a, 'b> FnCodegen<'a, 'b> {
    fn fresh_var(&mut self, ty: Ty) -> Variable {
        let var = Variable::new(self.next_var as usize);
        self.next_var += 1;
        self.builder.declare_var(var, ty_to_clif(ty, self.ptr_type));
        var
    }

    fn intern_string(&mut self, s: &str) -> Result<Value> {
        let mut bytes = s.as_bytes().to_vec();
        bytes.push(0);
        let data_name = format!("__yuri_str_{}", self.string_counter);
        self.string_counter += 1;

        let data_id = self
            .module
            .declare_data(&data_name, Linkage::Local, false, false)
            .map_err(|e| anyhow!("failed to declare string data: {e}"))?;

        let mut desc = DataDescription::new();
        desc.define(bytes.into_boxed_slice());
        self.module
            .define_data(data_id, &desc)
            .map_err(|e| anyhow!("failed to define string data: {e}"))?;

        let gv = self.module.declare_data_in_func(data_id, self.builder.func);
        Ok(self.builder.ins().global_value(self.ptr_type, gv))
    }

    fn to_float(&mut self, v: Value, ty: Ty) -> Value {
        match ty {
            Ty::Float => v,
            Ty::Int => self.builder.ins().fcvt_from_sint(types::F64, v),
            Ty::Str => unreachable!("string-to-float coercion is rejected before this point"),
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
        }
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
            // Mixed int/float or float/float: widen ints to float.
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
        match ty {
            Ty::Str => {
                self.builder.ins().call(self.runtime.print_str, &[val]);
            }
            Ty::Int => {
                self.builder.ins().call(self.runtime.print_int, &[val]);
            }
            Ty::Float => {
                self.builder.ins().call(self.runtime.print_float, &[val]);
            }
        }
    }

    fn compile_stmt(&mut self, stmt: &Stmt) -> Result<()> {
        match stmt {
            Stmt::Bond { name, value } => {
                let (val, ty) = self.compile_expr(value)?;
                let var = self.fresh_var(ty);
                self.builder.def_var(var, val);
                self.env.insert(name.clone(), (var, ty));
                Ok(())
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
                Ok(())
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
                for s in then_body {
                    self.compile_stmt(s)?;
                }
                self.builder.ins().jump(merge_block, &[]);

                self.builder.switch_to_block(else_block);
                self.builder.seal_block(else_block);
                if let Some(else_stmts) = else_body {
                    for s in else_stmts {
                        self.compile_stmt(s)?;
                    }
                }
                self.builder.ins().jump(merge_block, &[]);

                self.builder.switch_to_block(merge_block);
                self.builder.seal_block(merge_block);
                Ok(())
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
                for s in body {
                    self.compile_stmt(s)?;
                }

                let i_val2 = self.builder.use_var(i_var);
                let one = self.builder.ins().iconst(types::I64, 1);
                let next_i = self.builder.ins().iadd(i_val2, one);
                self.builder.def_var(i_var, next_i);
                self.builder.ins().jump(loop_head, &[]);

                self.builder.seal_block(loop_head);

                self.builder.switch_to_block(loop_exit);
                self.builder.seal_block(loop_exit);
                Ok(())
            }
        }
    }
}
