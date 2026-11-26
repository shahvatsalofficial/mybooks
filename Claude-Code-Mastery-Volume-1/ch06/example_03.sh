# INSECURE NAIVE IMPLEMENTATION (Vulnerable to Command Injection!)
function execute_test_command(user_arg) {
    # Dangerously interpolates raw user argument into bash subshell
    shell.exec("npm test -- " + user_arg);
}
