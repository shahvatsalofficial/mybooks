// Vulnerable Closure Capture
const [dashboardConfig, setDashboardConfig] = useState<HeavyConfigObject>(largeConfig);

useEffect(() => {
    const handleEvent = () => {
        // This closure captures the 'dashboardConfig' variable.
        // Even if the dashboard unmounts, if 'handleEvent' is registered
        // in a global emitter, 'dashboardConfig' is retained in memory.
        console.log("Active profile ID:", dashboardConfig.profileId);
    };

    globalEmitter.on("configSync", handleEvent);
    return () => {
        globalEmitter.off("configSync", handleEvent);
    };
}, [dashboardConfig]);
