const mongoose = require('mongoose');

const watch_next_schema = new mongoose.Schema({
    title: String,
    watch_next_list: [{idx: String, url_watch_next: String}]
}, { collection: 'tedz_data' });

module.exports = mongoose.model('watch_next', watch_next_schema);
