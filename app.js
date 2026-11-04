const STORAGE_KEY = 'task-board.tasks';

const defaultTasks = [
  { id: 1, title: 'Write the project brief' },
  { id: 2, title: 'Review the design draft' },
];

function newId() {
  return typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function loadTasks() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (Array.isArray(saved)) return saved;
  } catch (error) {
    // Storage blocked or data corrupted: fall back to the defaults.
  }
  return defaultTasks;
}

function saveTasks() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
  } catch (error) {
    // Storage blocked (e.g. private mode): the list still works for this visit.
  }
}

const tasks = loadTasks();

function render() {
  const list = document.getElementById('list');
  list.innerHTML = '';
  for (const task of tasks) {
    const li = document.createElement('li');
    li.textContent = task.title;
    list.appendChild(li);
  }
}

document.getElementById('add-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const input = document.getElementById('task-input');
  const title = input.value.trim();
  if (!title) return;
  tasks.push({ id: newId(), title });
  saveTasks();
  input.value = '';
  render();
});

render();
