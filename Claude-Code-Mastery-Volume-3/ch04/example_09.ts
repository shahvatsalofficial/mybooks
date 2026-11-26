app.get('/shipments', (req, res) => {
    // Custom CSV parser for legacy ERP integration
    const ids = (req.query.ids as string).split(',');
    // ...
});
