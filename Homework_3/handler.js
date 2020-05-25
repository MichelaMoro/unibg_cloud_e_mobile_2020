const connect_to_db = require('./db');

// GET BY TALK HANDLER

const watch_next= require('./Watch_next');

module.exports.get_by_watch_next = (event, context, callback) => {
    context.callbackWaitsForEmptyEventLoop = false;
    console.log('Received event:', JSON.stringify(event, null, 2));
    let body = {}
    if (event.body) {
        body = JSON.parse(event.body)
    }
    // set default
    if(!body.tag) {
        callback(null, {
                    statusCode: 500,
                    headers: { 'Content-Type': 'text/plain' },
                    body: 'Could not fetch the watch next talk. Tag is null.'
        })
    }
    
