app.get('/shipments', (req, res) => {
    const ids = req.query.ids as string[]; // FAILED TO PARSE CSV STRINGS
    // ...
});
