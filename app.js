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

// Returns a usable task from a stored entry, or null when the entry is corrupt.
function normalizeTask(entry) {
  if (entry === null || typeof entry !== 'object' || Array.isArray(entry)) return null;
  if (typeof entry.title !== 'string' || entry.title.trim() === '') return null;
  const id = entry.id;
  const hasId = (typeof id === 'number' && Number.isFinite(id)) ||
    (typeof id === 'string' && id !== '');
  return { id: hasId ? id : newId(), title: entry.title.trim() };
}

function loadTasks() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (Array.isArray(saved)) {
      const cleaned = saved.map(normalizeTask).filter(Boolean);
      if (cleaned.length > 0) return cleaned;
    }
  } catch (error) {
    // Storage blocked or data corrupted: fall back to the defaults.
  }
  // Return a copy: this page rewrites the list in place, and the fallback
  // must stay intact for the next load.
  return defaultTasks.slice();
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

function announce(message) {
  document.getElementById('status').textContent = message;
}

function taskCountLabel(count) {
  return `${count} ${count === 1 ? 'task' : 'tasks'}`;
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
  announce(`Added "${title}". ${taskCountLabel(tasks.length)} in the list.`);
});

// Another tab changed the shared list. Adopt it here as well, otherwise this
// tab's next save would silently overwrite the tasks it never saw.
window.addEventListener('storage', (event) => {
  // A null key means the whole storage area was cleared, so reload too.
  if (event.key !== null && event.key !== STORAGE_KEY) return;
  const next = loadTasks();
  tasks.length = 0;
  tasks.push(...next);
  render();
});

render();
