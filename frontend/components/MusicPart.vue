<template>
  <div class="row align-items-center mb-3 part-row">
    <!-- Part Controls (Left) -->
    <div class="col-md-2">
      <div class="part-control">
        <h5>{{ part.name }}</h5>
        <button class="btn btn-sm btn-primary" @click.stop="openPartMenu">Edit Part</button>
      </div>
    </div>

    <!-- Score Display (Right) -->
    <div class="col-md-10">
      <div class="score-wrapper" ref="scoreContainer"></div>
    </div>

    <!-- Part Edit Popup -->
    <div
      v-if="partMenuVisible"
      class="card p-2 shadow"
      :style="{
        position: 'fixed',
        left: menuPosition.x + 'px',
        top:  menuPosition.y + 'px',
        zIndex: 1050,
        width: '220px'
      }"
      @click.stop
    >
      <div class="mb-2">
        <label class="form-label small mb-1">Part Name</label>
        <input type="text" v-model="editablePartName" @input="updatePartName" class="form-control form-control-sm">
      </div>
      <button class="btn btn-danger btn-sm" @click="deletePart">Delete Part</button>
    </div>

    <!-- Note Edit Popup -->
    <div
      v-if="noteMenuVisible && selectedNote"
      class="card p-2 shadow"
      :style="{
        position: 'fixed',
        left: menuPosition.x + 'px',
        top:  menuPosition.y + 'px',
        zIndex: 1050,
        width: '200px'
      }"
      @click.stop
    >
      <div class="mb-2">
        <label class="form-label small mb-1">Pitch</label>
        <select v-model="selectedNote.pitch" class="form-select form-select-sm">
          <option v-for="p in ['C','D','E','F','G','A','B']" :key="p">{{ p }}</option>
        </select>
      </div>
      <div class="mb-2">
        <label class="form-label small mb-1">Octave</label>
        <select v-model="selectedNote.octave" class="form-select form-select-sm">
          <option v-for="o in [2,3,4,5,6]" :key="o">{{ o }}</option>
        </select>
      </div>
      <div class="mb-3">
        <label class="form-label small mb-1">Duration</label>
        <select v-model="selectedNote.duration" class="form-select form-select-sm">
          <option value="w">Whole</option>
          <option value="h">Half</option>
          <option value="q">Quarter</option>
          <option value="8">Eighth</option>
          <option value="16">16th</option>
        </select>
      </div>
      <div class="d-flex justify-content-between">
        <button class="btn btn-info btn-sm" @click="updateSelectedNote">Apply</button>
        <button class="btn btn-warning btn-sm" @click="deleteSelectedNote">Delete</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, toRaw } from 'vue';
import { Factory, Formatter, StaveNote } from 'vexflow'; // StaveNote might be needed for advanced features

const props = defineProps({
  part: Object,
  partIndex: Number,
});

const emit = defineEmits(['update:part', 'delete:part']);

const scoreContainer = ref(null);
const partMenuVisible = ref(false);
const noteMenuVisible = ref(false);
const menuPosition = ref({ x: 0, y: 0 });
const selectedNote = ref(null);
const editablePartName = ref(props.part.name);
const renderedNotesInfo = ref([]); // To store info about rendered notes

// Helper to parse the notes string into an array of objects
const parseNotesInput = (notesInputString) => {
  if (!notesInputString || notesInputString.trim() === '') return [];
  return notesInputString.split(',').map(noteString => {
    const trimmed = noteString.trim();
    const [pitchOctave, duration] = trimmed.split('/');
    const pitch = pitchOctave.slice(0, -1);
    const octave = parseInt(pitchOctave.slice(-1), 10);
    return { pitch, octave, duration, originalString: trimmed };
  });
};

const drawScore = async () => {
  if (!scoreContainer.value) return;
  scoreContainer.value.innerHTML = '';

  const factory = new Factory({
    renderer: { elementId: scoreContainer.value, width: 900, height: 150 },
  });

  const score = factory.EasyScore();
  const system = factory.System({ width: 900 });

  let voice;
  try {
    const notesString = props.part.notesInput && props.part.notesInput.trim() !== '' ? props.part.notesInput : 'B4/w/r';
    const notes = score.notes(notesString, { stem: 'up' });
    voice = score.voice(notes);
  } catch (e) {
    console.error(`Error parsing notes for part ${props.partIndex}:`, e);
    const notes = score.notes('B4/w/r', { stem: 'up' }); // Fallback
    voice = score.voice(notes);
  }

  system.addStave({ voices: [voice] }).addClef('treble').addTimeSignature('4/4');
  factory.draw();

  // After drawing, collect information about rendered notes
  renderedNotesInfo.value = [];
  const rawVoice = toRaw(voice);
  if (rawVoice && typeof rawVoice.getTickables === 'function') {
    rawVoice.getTickables().forEach((note, noteIndex) => {
      if (note.getBoundingBox) {
        const bbox = note.getBoundingBox();
        if (bbox) {
          renderedNotesInfo.value.push({
            noteIndex: noteIndex,
            x: bbox.getX(),
            y: bbox.getY(),
            width: bbox.getW(),
            height: bbox.getH(),
          });
        }
      }
    });
  }

  const svg = scoreContainer.value.querySelector('svg');
  if (svg) {
    svg.style.pointerEvents = 'auto'; // Make SVG clickable
    svg.addEventListener('click', (event) => handleClickOnScore(event, system.getStaves()[0]));
  }
};

const handleClickOnScore = (event, stave) => {
  const rect = event.currentTarget.getBoundingClientRect();
  const clickX = event.clientX - rect.left;
  const clickY = event.clientY - rect.top;

  // Check if an existing note was clicked
  for (const noteInfo of renderedNotesInfo.value) {
    if (
      clickX >= noteInfo.x &&
      clickX <= noteInfo.x + noteInfo.width &&
      clickY >= noteInfo.y &&
      clickY <= noteInfo.y + noteInfo.height
    ) {
      const notesArray = parseNotesInput(props.part.notesInput);
      // Make a deep copy for editing to avoid reactivity issues
      selectedNote.value = JSON.parse(JSON.stringify(notesArray[noteInfo.noteIndex]));
      selectedNote.value.noteIndex = noteInfo.noteIndex;
      
      menuPosition.value = { x: event.clientX + 5, y: event.clientY + 5 };
      noteMenuVisible.value = true;
      partMenuVisible.value = false; // Hide other menu
      event.stopPropagation();
      return;
    }
  }
  closeMenus();
};

const updateSelectedNote = () => {
  if (!selectedNote.value) return;
  
  const notesArray = parseNotesInput(props.part.notesInput);
  const noteToUpdate = selectedNote.value;
  
  notesArray[noteToUpdate.noteIndex] = {
    ...notesArray[noteToUpdate.noteIndex],
    pitch: noteToUpdate.pitch,
    octave: noteToUpdate.octave,
    duration: noteToUpdate.duration,
  };

  const newNotesInput = notesArray.map(n => `${n.pitch}${n.octave}/${n.duration}`).join(', ');
  emit('update:part', { ...props.part, notesInput: newNotesInput });
  closeMenus();
};

const deleteSelectedNote = () => {
  if (!selectedNote.value) return;

  const notesArray = parseNotesInput(props.part.notesInput);
  notesArray.splice(selectedNote.value.noteIndex, 1);

  const newNotesInput = notesArray.map(n => `${n.pitch}${n.octave}/${n.duration}`).join(', ');
  emit('update:part', { ...props.part, notesInput: newNotesInput });
  closeMenus();
};

const openPartMenu = (event) => {
  const rect = event.target.getBoundingClientRect();
  menuPosition.value = { x: rect.left, y: rect.bottom + 5 };
  partMenuVisible.value = true;
  noteMenuVisible.value = false; // Hide other menu
};

const updatePartName = () => {
  emit('update:part', { ...props.part, name: editablePartName.value });
};

const deletePart = () => {
  emit('delete:part', props.partIndex);
  partMenuVisible.value = false;
};

const closeMenus = () => {
  partMenuVisible.value = false;
  noteMenuVisible.value = false;
  selectedNote.value = null;
};

onMounted(() => {
  drawScore();
  window.addEventListener('click', closeMenus);
});

watch(() => props.part, () => {
  editablePartName.value = props.part.name;
  drawScore();
}, { deep: true });

</script>

<style scoped>
.part-row {
  border-bottom: 1px solid #eee;
  padding-bottom: 1rem;
}
.score-wrapper {
  min-height: 120px; /* Ensure wrapper has height for Vexflow to draw into */
}
</style>