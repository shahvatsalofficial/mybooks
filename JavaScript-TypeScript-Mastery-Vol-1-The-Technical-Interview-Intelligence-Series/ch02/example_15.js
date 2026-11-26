// Virtual DOM Node Creator
function h(type, props, ...children) {
    return {
        type,
        props: props || {},
        children: children.flat(),
        key: props && props.key ? props.key : null
    };
}

// Convert a VDOM object tree into a real browser DOM node
function createRealDOMNode(vnode) {
    if (typeof vnode === 'string' || typeof vnode === 'number') {
        return document.createTextNode(vnode);
    }

    const element = document.createElement(vnode.type);
    
    // Assign properties and events
    Object.keys(vnode.props).forEach(name => {
        if (name.startsWith('on') && typeof vnode.props[name] === 'function') {
            const eventName = name.substring(2).toLowerCase();
            element.addEventListener(eventName, vnode.props[name]);
        } else if (name !== 'key') {
            element.setAttribute(name, vnode.props[name]);
        }
    });

    // Recursively append children
    vnode.children.forEach(child => {
        element.appendChild(createRealDOMNode(child));
    });

    return element;
}

// The core diffing and patching engine
function patchDOM(parent, newVNode, oldVNode, index = 0) {
    // Case 1: Old node does not exist, append the new node
    if (!oldVNode) {
        parent.appendChild(createRealDOMNode(newVNode));
        return;
    }

    // Case 2: New node does not exist, remove the old node
    if (!newVNode) {
        parent.removeChild(parent.childNodes[index]);
        return;
    }

    // Case 3: Node types have changed, replace the node entirely
    if (typeof newVNode !== typeof oldVNode || newVNode.type !== oldVNode.type) {
        parent.replaceChild(createRealDOMNode(newVNode), parent.childNodes[index]);
        return;
    }

    // Case 4: Both are text nodes, update content if they differ
    if (typeof newVNode === 'string' || typeof newVNode === 'number') {
        if (newVNode !== oldVNode) {
            parent.childNodes[index].nodeValue = newVNode;
        }
        return;
    }

    // Case 5: Element nodes are identical, update properties and diff children
    const element = parent.childNodes[index];
    updateNodeProps(element, newVNode.props, oldVNode.props);
    
    // Diff children recursively using key-based heuristic updates
    diffVNodeChildren(element, newVNode.children, oldVNode.children);
}

// Property updater
function updateNodeProps(element, newProps, oldProps) {
    // Remove old properties
    Object.keys(oldProps).forEach(name => {
        if (!newProps.hasOwnProperty(name)) {
            if (name.startsWith('on')) {
                const eventName = name.substring(2).toLowerCase();
                element.removeEventListener(eventName, oldProps[name]);
            } else {
                element.removeAttribute(name);
            }
        }
    });

    // Set new or modified properties
    Object.keys(newProps).forEach(name => {
        if (newProps[name] !== oldProps[name]) {
            if (name.startsWith('on')) {
                const eventName = name.substring(2).toLowerCase();
                element.removeEventListener(eventName, oldProps[name]);
                element.addEventListener(eventName, newProps[name]);
            } else if (name !== 'key') {
                element.setAttribute(name, newProps[name]);
            }
        }
    });
}

// Child reconciliation using key mapping mechanics
function diffVNodeChildren(element, newChildren, oldChildren) {
    const maxLen = Math.max(newChildren.length, oldChildren.length);
    for (let i = 0; i < maxLen; i++) {
        patchDOM(element, newChildren[i], oldChildren[i], i);
    }
}
