function queueTasksFixed() {
    for (let i = 0; i < 5; i++) {
        setTimeout(function() {
            console.log(i);
        }, 100);
    }
}
queueTasksFixed(); // Prints 0, 1, 2, 3, 4
