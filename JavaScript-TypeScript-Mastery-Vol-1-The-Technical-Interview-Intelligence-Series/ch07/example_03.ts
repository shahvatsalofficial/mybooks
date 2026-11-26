// Vulnerable DOM Pointer Reference
const detachedNodeRef = useRef<HTMLDivElement | null>(null);

useEffect(() => {
    detachedNodeRef.current = document.getElementById("analytics-panel") as HTMLDivElement;
    
    return () => {
        // The element is removed from the DOM by React, but detachedNodeRef.current
        // still points to the physical DOM node. The V8 engine cannot reclaim the element
        // or any of its child DOM elements.
    };
}, []);
