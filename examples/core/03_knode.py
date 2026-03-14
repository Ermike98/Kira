from kira.core.kcontext import KContext
from kira.knodes.knode import KNode
from kira.kdata.kdata import KData, KDataValue
from kira.kdata.kliteral import KLiteral
from kira.core.kobject import KObject
from kira.ktypeinfo.any_type import KAnyTypeInfo

class AddOneNode(KNode):
    def __init__(self):
        # inputs=['in_val'], outputs=['out_val']
        super().__init__(name="AddOne", inputs=["in_val"], outputs=["out_val"])

    def call(self, inputs: list[KObject], context: KContext) -> list[KDataValue]:
        # inputs[0] is expected to be a KData with a numeric value
        in_data = inputs[0]
        if isinstance(in_data, KData) and hasattr(in_data.value, 'value'):
            val = in_data.value.value
            return [KLiteral(val + 1)]
        return [KLiteral(0)]

def main():
    print("--- Kira Core Example: KNode ---")
    
    ctx = KContext()
    node = AddOneNode()
    
    # Define inputs
    input_data = {"in_val": KData("input", KLiteral(10))}
    
    # Execute node
    print(f"Calling node {node.name} with input 10...")
    outputs = node(input_data, ctx)
    
    for out in outputs:
        print(f"Output '{out.name}': {out.value.value}")

if __name__ == "__main__":
    main()
