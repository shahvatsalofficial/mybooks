// DANGEROUS IMPLEMENTATION: Conditional Hook Execution
function VulnerableDashboard({ isAdmin }) {
    const [userId, setUserId] = useState("USR_99");

    if (isAdmin) {
        // Condition alters execution sequence!
        useEffect(() => {
            fetchAdminLogs();
        }, []);
    }

    const [sessionToken, setSessionToken] = useState("TOK_ABC");
}
