const moods = document.querySelectorAll('.mood');
const note = document.getElementById('note');
const saveBtn = document.getElementById('saveBtn');
const entries = document.getElementById('entries');

let selectedMood = null;

moods.forEach(btn => {
  btn.addEventListener('click', () => {
    selectedMood = btn.dataset.value;
    moods.forEach(b => b.style.opacity = '0.5');
    btn.style.opacity = '1';
  });
});

saveBtn.addEventListener('click', () => {
  if (!selectedMood) {
    alert('Please select a mood!');
    return;
  }

  const today = new Date();
  const todayStr = `${today.getDate()}/${today.getMonth() + 1}/${today.getFullYear()}`;

  const entry = {
    date: todayStr,
    mood: selectedMood,
    note: note.value || '(no note)'
  };

  let data = JSON.parse(localStorage.getItem('moods')) || [];

  // Check if an entry already exists for today
  const existingIndex = data.findIndex(e => e.date === todayStr);
  if (existingIndex !== -1) {
    data[existingIndex] = entry; // Update existing entry
    alert('Mood updated for today!');
  } else {
    data.push(entry); // Add new entry
    alert('Mood saved successfully!');
  }

  localStorage.setItem('moods', JSON.stringify(data));
  displayEntries();

  note.value = '';
  selectedMood = null;
  moods.forEach(b => b.style.opacity = '1');
});

function displayEntries() {
  entries.innerHTML = '';
  const data = JSON.parse(localStorage.getItem('moods')) || [];
  data.slice().reverse().forEach(e => {
    const li = document.createElement('li');
    li.textContent = `${e.date} → Mood: ${e.mood} | Note: ${e.note}`;
    entries.appendChild(li);
  });
}

displayEntries();