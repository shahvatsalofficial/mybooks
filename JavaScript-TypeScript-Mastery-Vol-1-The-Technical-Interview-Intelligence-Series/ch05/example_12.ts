useEffect(() => {
    const handleResize = () => console.log(window.innerWidth);
    window.addEventListener('resize', handleResize);

    // CLEANUP: Removes the listener to prevent memory leaks and stale event handlers
    return () => window.removeEventListener('resize', handleResize);
}, []);
