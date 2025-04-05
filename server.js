const express = require('express');
const app = express();
const http = require('http').createServer(app);
const io = require('socket.io')(http);

app.use(express.static('public'));

// Store users by socket ID
const users = {};

io.on('connection', (socket) => {
  console.log(`User connected: ${socket.id}`);

  // New user joins
  socket.on('new-user', (user) => {
    users[socket.id] = { ...user, socketId: socket.id };
    io.emit('update-users', Object.values(users));
  });

  // Start a study session
  socket.on('start-session', ({ partnerUsername }) => {
    const user = users[socket.id];
    const partner = Object.values(users).find(u => u.username === partnerUsername);
    if (partner && partner.socketId !== socket.id) {
      io.to(partner.socketId).emit('session-started', {
        partner: user,
        mode: user.studyPreference
      });
      socket.emit('session-started', {
        partner,
        mode: user.studyPreference
      });
    }
  });

  // Send notes during session
  socket.on('send-note', ({ partnerUsername, note }) => {
    const partner = Object.values(users).find(u => u.username === partnerUsername);
    if (partner) {
      io.to(partner.socketId).emit('receive-note', {
        from: users[socket.id].username,
        note
      });
    }
  });

  // Report user
  socket.on('report-user', ({ reportedUsername }) => {
    const user = users[socket.id];
    user.reports.push(reportedUsername);
    console.log(`${user.username} reported ${reportedUsername}`);
  });

  // Block user
  socket.on('block-user', ({ blockedUsername }) => {
    const user = users[socket.id];
    user.blocked.push(blockedUsername);
    io.emit('update-users', Object.values(users));
  });

  // Disconnect
  socket.on('disconnect', () => {
    console.log(`User disconnected: ${socket.id}`);
    delete users[socket.id];
    io.emit('update-users', Object.values(users));
  });
});

const HOST = '0.0.0.0';
const PORT = 3000;

http.listen(PORT, HOST, () => {
  console.log(`Gyancho server running at http://${HOST}:${PORT}`);
});
