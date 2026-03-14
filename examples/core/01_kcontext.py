from kira.core.kcontext import KContext
from kira.kdata.kdata import KData
from kira.kdata.kliteral import KLiteral

def main():
    print("--- Kira Core Example: KContext ---")
    
    # 1. Initialize KContext
    # The context is the environment where objects (KData, KNodes) live.
    ctx = KContext()
    print("KContext initialized.")

    # 2. Register objects manually (though usually done via evaluation)
    data1 = KData("my_var", KLiteral(42))
    ctx.register_object(data1)
    print(f"Registered: {data1.name} = {data1.value.value}")

    # 3. Retrieve objects
    retrieved = ctx.get_object("my_var")
    if retrieved:
        print(f"Retrieved {retrieved.name}: {retrieved}")

    # 4. Check all symbols
    print(f"All symbols in context: {list(ctx._objects.keys())}")

if __name__ == "__main__":
    main()
