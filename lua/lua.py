# YuriLang Inline Lua (Runtime) v1.7.0
#
# Features:
#   @lua [block]        -> multi-line Lua execution
#   @lua "exprs"        -> single line Lua expression
#   yuri.<var>          -> reads Yurilang variables from Lua
#   yuri.<var> = x      -> write back to Yurilang
#   yurilang.get(k)     -> GET
#   yurilang.set(k,v)   -> SET
#   yurilang.call(f)    -> call a (@ship) function from Lua
#
#   Copyrights Reserved 2026 Kazooki123
#   Read LICENSE for more information

try:
    from lupa.lua54 import LuaRuntime

    LUPA_AVAILABLE = True
except ImportError:
    try:
        from lupa import LuaRuntime

        LUPA_AVAILABLE = True
    except ImportError:
        LUPA_AVAILABLE = False
        LuaRuntime = None


class LuaError(Exception):
    pass


class YuriLuaRuntime:
    def __init__(self, variables, functions, run_node_fn, eval_fn):
        if not LUPA_AVAILABLE:
            raise LuaError(
                "\n💔 @lua - lupa not installed!\n"
                " | She tried to speak Lua but couldn't find the runtime..\n"
                " |> Hint: pip install lupa\n"
                "          uv pip install lupa --system (uv)\n"
            )

        self.variables = variables
        self.functions = functions
        self.run_node = run_node_fn
        self.evaluate = eval_fn
        self._lua = None

    def _get_runtime(self):
        if self._lua is not None:
            return self._lua

        self._lua = LuaRuntime(unpack_returned_tuples=True, encoding=None)

        self._setup_bridge()
        return self._lua

    def _setup_bridge(self):
        lua = self._lua
        variables = self.variables
        functions = self.functions
        run_node = self.run_node
        evaluate = self.evaluate

        def yuri_get(key):
            k = _decode(key)
            val = variables.get(k)
            return _to_lua(val)

        def yuri_set(key, value):
            k = _decode(key)
            variables[k] = _from_lua(value)

        def yuri_call(func_name, *args):
            fname = _decode(func_name)
            if fname not in functions:
                raise LuaError(
                    f"\n💔 yurilang.call - '{fname}' not found!\n"
                    f" | She called a @ship that doesn't exist.\n"
                    f" |> Hint: Define @ship {fname} before the @lua block.\n"
                )
            entry = functions[fname]
            params = entry[0]
            body = entry[1]

            from src.interpreter import ReturnSignal

            old_vars = variables.copy()

            lua_args = [_from_lua(a) for a in args]
            for i, param in enumerate(params):
                if i < len(lua_args):
                    variables[param] = lua_args[i]

            result = None
            for child in body:
                ret = run_node(child)
                if isinstance(ret, ReturnSignal):
                    result = ret.value
                    break

            variables.clear()
            variables.update(old_vars)
            return _to_lua(result)

        def yuri_confess(*args):
            decoded = [str(_from_lua(a)) for a in args]
            print(" ".join(decoded))

        def yuri_whisper(*args):
            GREY = "\033[38;5;245m"
            RESET = "\033[0m"
            decoded = [str(_from_lua(a)) for a in args]
            print(f"{GREY}{' '.join(decoded)}{RESET}")

        def yuri_type(key):
            k = _decode(key)
            val = variables.get(k)
            from src.etc.types import type_name

            return type_name(val)

        lua.execute("""
            yurilang = {}
        """)
        lua.globals().yurilang["get"] = yuri_get
        lua.globals().yurilang["set"] = yuri_set
        lua.globals().yurilang["call"] = yuri_call
        lua.globals().yurilang["confess"] = yuri_confess
        lua.globals().yurilang["whisper"] = yuri_whisper
        lua.globals().yurilang["type"] = yuri_type

        lua.execute("""
            yuri = setmetatable({}, {
                __index = function(t, k)
                    return yurilang.get(k)
                end,
                __newindex = function(t, k, v)
                    yurilang.set(k, v)
                end,
                __tostring = function(t)
                    return "Yurilang variable bridge"
                end
            })
        """)

        lua.execute("""
            function confess(...)
                yurilang.confess(...)
            end
            
            function whisper(...)
                yurilang.whisper(...)
            end
            
            function ship(...)
                return yurilang.call(name, ...)
            end
            
            bond = yurilang.set
            recall = yurilang.get
        """)

    def execute_block(self, lua_code, source_line=None):
        lua = self._get_runtime()
        self._sync_to_lua(lua)

        lua_code = lua_code.strip().lstrip(":").strip()

        if not lua_code:
            return

        try:
            lua.execute(lua_code)
        except Exception as e:
            raise LuaError(
                "\n💔 @lua block - Lua error\n\n"
                " | She got confused speaking Lua.\n\n"
                f" | {str(e)}\n\n"
                " |> Hint: Check your Lua syntax inside the @lua block.\n"
            )

        self._sync_from_lua(lua)

    def execute_expr(self, lua_expr):
        lua = self._get_runtime()
        self._sync_to_lua(lua)

        try:
            wrapped = f"__yuri_result__ = (function() {lua_expr} end)()"
            lua.execute(wrapped)
            result = lua.globals().__yuri_result__
        except Exception:
            try:
                lua.execute(lua_expr)
                result = None
            except Exception as e2:
                raise LuaError(
                    "\n💔 @lua expression - Lua error\n\n"
                    f" | {str(e2)}\n\n"
                    " |> Hint Use 'return' for expressions:\n\n"
                    '         @bond val = @lua "return 2 ^ 10"\n'
                )

        self._sync_from_lua(lua)
        return _from_lua(result)

    def _sync_to_lua(self, lua):
        for name, val in self.variables.items():
            if name.startswith("__"):
                continue
            try:
                lua.globals()[name] = _to_lua(val)
            except Exception:
                pass

    def _sync_from_lua(self, lua):
        for name in list(self.variables.keys()):
            if name.startswith("__"):
                continue
            try:
                lua_val = lua.globals()[name]
                if lua_val is not None:
                    self.variables[name] = _from_lua(lua_val)
            except Exception:
                pass


def _decode(val):
    if isinstance(val, bytes):
        return val.decode("utf-8")
    return str(val) if val is not None else ""


def _to_lua(val):
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        return val
    if isinstance(val, dict):
        return val
    return str(val)


def _from_lua(val):
    if val is None:
        return None
    if isinstance(val, bytes):
        return val.decode("utf-8")
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        if isinstance(val, float) and val.is_integer():
            return int(val)
        return val
    if isinstance(val, str):
        return val

    try:
        items = list(val.values())
        return items
    except Exception:
        pass

    return val


_runtime_instance = None


def get_lua_runtime(variables, functions, run_node_fn, eval_fn):
    global _runtime_instance
    if _runtime_instance is None:
        _runtime_instance = YuriLuaRuntime(variables, functions, run_node_fn, eval_fn)
    else:
        _runtime_instance.variables = variables
        _runtime_instance.functions = functions
        _runtime_instance.run_node = run_node_fn
        _runtime_instance.evaluate = eval_fn
    return _runtime_instance


def reset_lua_runtime():
    global _runtime_instance
    _runtime_instance = None
