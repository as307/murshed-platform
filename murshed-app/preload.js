const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('murshed', {
  stats: () => ipcRenderer.invoke('dashboard:stats'),
  service: () => ipcRenderer.invoke('dashboard:service'),
  log: () => ipcRenderer.invoke('dashboard:log'),
  restart: () => ipcRenderer.invoke('dashboard:restart'),
  reveal: (file) => ipcRenderer.invoke('dashboard:reveal', file),
});
