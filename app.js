const tasks = [
  { id: 1, title: 'Write the project brief' },
  { id: 2, title: 'Review the design draft' },
];

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
  tasks.push({ id: Date.now(), title });
  input.value = '';
  render();
});

render();
