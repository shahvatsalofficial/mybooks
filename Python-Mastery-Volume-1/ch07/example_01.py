class Node:
    def __init__(self, name: str) -> None:
        self.name = name
        self.peer: Node | None = None

# Step 1: Allocate nodes
a = Node("A") # a.ob_refcnt = 1
b = Node("B") # b.ob_refcnt = 1

# Step 2: Form circular link
a.peer = b    # b.ob_refcnt = 2
b.peer = a    # a.ob_refcnt = 2

# Step 3: Delete local variables
del a         # a.ob_refcnt drops to 1
del b         # b.ob_refcnt drops to 1
