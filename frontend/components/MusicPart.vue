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
      <div class="measure-numbers d-flex justify-content-between mt-1">
        <div
          v-for="measure in measures"
          :key="measure.number"
          class="measure-number"
        >
          {{ measure.number }}
        </div>
      </div>
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
      <button class="btn btn-secondary btn-sm mb-2" @click="copyPartJson">Copy JSON</button>
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
      <div class="form-check mb-2">
        <input id="restCheck" type="checkbox" class="form-check-input" v-model="selectedNote.rest">
        <label for="restCheck" class="form-check-label small">Rest</label>
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
const measures = ref([]);

// Helper to parse the notes string into an array of objects
// Invalid or incomplete notes are ignored so that drawing never throws
const parseNotesInput = (notesInputString) => {
  if (!notesInputString || notesInputString.trim() === '') return [];
  return notesInputString
    .replace(/\|/g, ',')
    .split(',')
    .map(noteString => {
      const trimmed = noteString.trim();
      if (!trimmed) return null;
      const [pitchOctave, duration, restFlag] = trimmed.split('/');
      if (!pitchOctave || !duration) return null;
      const pitch = pitchOctave.slice(0, -1);
      const octave = parseInt(pitchOctave.slice(-1), 10);
      if (!pitch || isNaN(octave)) return null;
      return {
        pitch,
        octave,
        duration,
        rest: restFlag === 'r',
        originalString: trimmed
      };
    })
    .filter(Boolean)
    .map((n, idx) => ({ ...n, noteIndex: idx }));
};

// Split parsed notes into measures of 4 beats (4/4). Missing beats are filled with a rest.
const splitIntoMeasures = (notesArray) => {
  const beatsPerMeasure = 4;
  const durationMap = { w: 4, h: 2, q: 1, '8': 0.5, '16': 0.25 };
  const measures = [];
  let currentMeasure = [];
  let currentBeats = 0;
  let idx = 0;

  const pushMeasure = () => {
    if (currentBeats < beatsPerMeasure && currentBeats > 0) {
      let remaining = beatsPerMeasure - currentBeats;
      const restDurations = [
        { beats: 4, duration: 'w' },
        { beats: 2, duration: 'h' },
        { beats: 1, duration: 'q' },
        { beats: 0.5, duration: '8' },
        { beats: 0.25, duration: '16' },
      ];
      for (const rest of restDurations) {
        while (remaining >= rest.beats - 1e-8) {
          currentMeasure.push({ pitch: 'B', octave: 4, duration: rest.duration, rest: true });
          remaining -= rest.beats;
        }
      }
    }
    if (currentMeasure.length === 0) {
      currentMeasure.push({ pitch: 'B', octave: 4, duration: 'w', rest: true });
    }
    measures.push(currentMeasure);
    currentMeasure = [];
    currentBeats = 0;
  };

  notesArray.forEach(note => {
    const beats = durationMap[note.duration] || 0;
    if (currentBeats + beats > beatsPerMeasure) {
      pushMeasure();
    }
    currentMeasure.push({ ...note, originalIndex: idx });
    currentBeats += beats;
    if (currentBeats === beatsPerMeasure) {
      pushMeasure();
    }
    idx += 1;
  });

  if (currentMeasure.length || measures.length === 0) {
    pushMeasure();
  }

  return measures;
};

const drawScore = async () => {
  if (!scoreContainer.value) return;
  scoreContainer.value.innerHTML = '';

  const factory = new Factory({
    renderer: { elementId: scoreContainer.value, width: 900, height: 150 },
  });

  const score = factory.EasyScore();
  const system = factory.System({ width: 900 });

  const notesArray = parseNotesInput(props.part.notesInput);
  const measuresArray = splitIntoMeasures(notesArray);
  measures.value = measuresArray.map((m, idx) => ({ number: idx + 1, notes: m }));
  const notesString = measures.value
    .map(measure =>
      measure.notes
        .map(n => `${n.pitch}${n.octave}/${n.duration}${n.rest ? '/r' : ''}`)
        .join(', ')
    )
    .join(' | ');

  let voice;
  try {
    const parsedNotes = score.notes(notesString || 'B4/w/r', { stem: 'up' });
    voice = score.voice(parsedNotes);
  } catch (e) {
    console.error(`Error parsing notes for part ${props.partIndex}:`, e);
    const fallback = score.notes('B4/w/r', { stem: 'up' });
    voice = score.voice(fallback);
  }

  system.addStave({ voices: [voice] })
    .addClef('treble')
    .addTimeSignature('4/4');

  factory.draw();

  // After drawing, collect information about rendered notes
  renderedNotesInfo.value = [];
  const allRenderedNotes = measuresArray.flat();
  const rawVoice = toRaw(voice);
  if (rawVoice && typeof rawVoice.getTickables === 'function') {
    let renderedIdx = 0;
    rawVoice.getTickables().forEach((note) => {
      if (note.getCategory && note.getCategory() === 'barnotes') return;
      const noteData = allRenderedNotes[renderedIdx];
      renderedIdx += 1;
      if (noteData && note.getBoundingBox) {
        const bbox = note.getBoundingBox();
        if (bbox) {
          renderedNotesInfo.value.push({
            noteIndex: noteData.originalIndex,
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
    rest: noteToUpdate.rest,
  };

  const plainNotes = notesArray.map(n => ({ pitch: n.pitch, octave: n.octave, duration: n.duration, rest: n.rest }));
  const newMeasures = splitIntoMeasures(plainNotes);
  const newNotesInput = newMeasures
    .map(m => m.map(n => `${n.pitch}${n.octave}/${n.duration}${n.rest ? '/r' : ''}`).join(', '))
    .join(' | ');
  emit('update:part', { ...props.part, notesInput: newNotesInput });
  closeMenus();
};

const deleteSelectedNote = () => {
  if (!selectedNote.value) return;

  const notesArray = parseNotesInput(props.part.notesInput);
  notesArray.splice(selectedNote.value.noteIndex, 1);

  const plainNotes = notesArray.map(n => ({ pitch: n.pitch, octave: n.octave, duration: n.duration, rest: n.rest }));
  const newMeasures = splitIntoMeasures(plainNotes);
  const newNotesInput = newMeasures
    .map(m => m.map(n => `${n.pitch}${n.octave}/${n.duration}${n.rest ? '/r' : ''}`).join(', '))
    .join(' | ');
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

const getPartJson = () => {
  return JSON.stringify(toRaw(props.part), null, 2);
};

const copyPartJson = async () => {
  try {
    await navigator.clipboard.writeText(getPartJson());
    alert('Part JSON copied to clipboard');
  } catch (err) {
    console.error('Failed to copy JSON:', err);
    alert(getPartJson());
  }
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
.measure-number {
  flex: 1;
  text-align: center;
  font-size: 0.8rem;
}
</style>