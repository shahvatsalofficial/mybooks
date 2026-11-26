// DANGER: Leaks file descriptors and memory if either stream throws an error
readableSource.pipe(transformStream).pipe(writableTarget);
