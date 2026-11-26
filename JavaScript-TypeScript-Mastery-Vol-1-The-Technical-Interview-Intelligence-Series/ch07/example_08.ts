useEffect(() => {
    const interval = setInterval(() => {
        console.log("Fetch metric under configuration ID:", config.id);
    }, 1000);
}, [config]);
