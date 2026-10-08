const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');
const dropzoneContent = document.getElementById('dropzone-content');
const previewImg = document.getElementById('preview-img');
const btnAnalyze = document.getElementById('btn-analyze');
const uploadForm = document.getElementById('upload-form');
const resultPanel = document.getElementById('result-panel');
const errorPanel = document.getElementById('error-panel');
const errorText = document.getElementById('error-text');
const btnReset = document.getElementById('btn-reset');

let selectedFile = null;

function showPreview(file) {
  selectedFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewImg.hidden = false;
    dropzoneContent.hidden = true;
    btnAnalyze.disabled = false;
  };
  reader.readAsDataURL(file);
}

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) showPreview(fileInput.files[0]);
});

['dragover', 'dragenter'].forEach(evt => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add('drag-over');
  });
});
['dragleave', 'drop'].forEach(evt => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove('drag-over');
  });
});
dropzone.addEventListener('drop', (e) => {
  const file = e.dataTransfer.files[0];
  if (file) showPreview(file);
});

uploadForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!selectedFile) return;

  btnAnalyze.disabled = true;
  btnAnalyze.textContent = 'Checking…';
  errorPanel.hidden = true;
  resultPanel.hidden = true;

  const formData = new FormData();
  formData.append('file', selectedFile);

  try {
    const res = await fetch('/predict', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || 'Something went wrong reading that image.');
    }

    renderResult(data);
  } catch (err) {
    errorText.textContent = err.message;
    errorPanel.hidden = false;
  } finally {
    btnAnalyze.disabled = false;
    btnAnalyze.textContent = 'Check this leaf';
  }
});

function renderResult(data) {
  const label = data.class.replace(/_/g, ' ');
  const isHealthy = data.class.toLowerCase().includes('healthy');

  document.getElementById('result-label').textContent = label;

  const badge = document.getElementById('result-badge');
  badge.textContent = isHealthy ? 'Looks healthy' : 'Possible disease';
  badge.className = 'result-badge ' + (isHealthy ? 'healthy' : 'disease');

  const pct = Math.round(data.confidence * 100);
  document.getElementById('confidence-fill').style.width = pct + '%';
  document.getElementById('confidence-pct').textContent = pct + '%';

  document.getElementById('advice-text').textContent = data.precaution;

  const list = document.getElementById('breakdown-list');
  list.innerHTML = '';
  data.top5.forEach(item => {
    const li = document.createElement('li');
    const name = document.createElement('span');
    name.textContent = item.class.replace(/_/g, ' ');
    const val = document.createElement('span');
    val.textContent = Math.round(item.confidence * 100) + '%';
    li.appendChild(name);
    li.appendChild(val);
    list.appendChild(li);
  });

  resultPanel.hidden = false;
  resultPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

btnReset.addEventListener('click', () => {
  selectedFile = null;
  fileInput.value = '';
  previewImg.hidden = true;
  dropzoneContent.hidden = false;
  btnAnalyze.disabled = true;
  resultPanel.hidden = true;
});
