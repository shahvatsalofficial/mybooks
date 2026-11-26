function queueTasks() {
    for (var i = 0; i < 5; i++) {
        setTimeout(function() {
            console.log(i);
        }, 100);
    }
}
queueTasks(); // Prints 5, 5, 5, 5, 5
