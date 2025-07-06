<template>
  <div class="container-fluid mt-3">
    <div class="d-flex justify-content-between align-items-center mb-2">
      <h1>MusicSheet Editor</h1>
      <div>
        <button @click="addPart" class="btn btn-outline-secondary btn-sm me-2">Add Part</button>
        <button @click="removeLastPart" class="btn btn-outline-danger btn-sm">Remove Last Part</button>
      </div>
    </div>
    <div class="score-wrapper">
      <ClientOnly>
        <div ref="scoreContainer" id="score-container"></div>
        <!-- ★ ポップアップメニュー -->
        <div
          v-if="menuVisible && selectedNote"
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
            <select v-model="parts[selectedNote.partIndex].selectedPitch" class="form-select form-select-sm">
              <option v-for="p in ['C','D','E','F','G','A','B']" :key="p">{{ p }}</option>
            </select>
          </div>

          <div class="mb-2">
            <label class="form-label small mb-1">Octave</label>
            <select v-model="parts[selectedNote.partIndex].selectedOctave" class="form-select form-select-sm">
              <option v-for="o in [2,3,4,5,6]" :key="o">{{ o }}</option>
            </select>
          </div>

          <div class="mb-3">
            <label class="form-label small mb-1">Duration</label>
            <select v-model="parts[selectedNote.partIndex].selectedDuration" class="form-select form-select-sm">
              <option value="w">Whole</option>
              <option value="h">Half</option>
              <option value="q">Quarter</option>
              <option value="8">Eighth</option>
              <option value="16">16th</option>
            </select>
          </div>

          <div class="d-flex justify-content-between">
            <button class="btn btn-info btn-sm" @click="updateSelectedNote">適用</button>
            <button class="btn btn-warning btn-sm" @click="deleteSelectedNote">削除</button>
          </div>
        </div>
      <div
          v-if="partMenuVisible && selectedPart"
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
            <input type="text" v-model="selectedPart.name" @input="updatePartName" class="form-control form-control-sm">
          </div>
          <button class="btn btn-danger btn-sm" @click="deleteSelectedPart">Delete Part</button>
        </div>

      </ClientOnly>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, toRaw, nextTick } from 'vue';
import { Factory, Stave, StaveNote, Voice, Formatter } from 'vexflow';

const { $api } = useNuxtApp(); // apiインスタンスをuseNuxtAppから取得

const parts = ref([
  { name: 'Part 1', notesInput: 'C4/q, D4/q, E4/q, F4/q', selectedPitch: 'C', selectedOctave: 4, selectedDuration: 'q' },
]);
const scoreContainer = ref(null);
const scoreId = ref(null);
const vexFlowSystem = ref(null); // To store the VexFlow System
const vexFlowStaves = ref([]); // To store the VexFlow Stave objects
const vexFlowVoices = ref([]); // To store the VexFlow Voice objects
const renderedNotesInfo = ref([]); // To store information about rendered notes for hit testing
const selectedNote = ref(null); // To store the currently selected note
const partMenuVisible = ref(false);
const selectedPart = ref(null);
// ★ script setup 内
const menuVisible     = ref(false);
const menuPosition    = ref({ x: 0, y: 0 });   // 画面座標で管理



const parseNotesInput = (notesInputString) => {
  if (!notesInputString) return [];
  return notesInputString.split(', ').map(noteString => {
    const [pitchOctave, duration] = noteString.split('/');
    const pitch = pitchOctave.slice(0, -1);
    const octave = parseInt(pitchOctave.slice(-1));
    return { pitch, octave, duration, originalString: noteString };
  });
};

const handleClickOnScore = (event) => {
  const canvas = event.currentTarget;
  const rect = canvas.getBoundingClientRect();
  const clickX = event.clientX - rect.left;
  const clickY = event.clientY - rect.top;

  console.log(`Clicked at: x=${clickX}, y=${clickY}`);

  // Check if the click was on a stave connector or clef area (i.e., the beginning of a part)
  let clickedStaveArea = false;
  const partHeaderWidth = 100; // Define a fixed width for the part header area (clef, time signature, etc.)

  for (let i = 0; i < vexFlowStaves.value.length; i++) {
    const stave = vexFlowStaves.value[i];
    // Check if the click is within the vertical bounds of the stave and within the fixed header width
    if (clickY >= stave.getY() && clickY <= stave.getBottomY() && clickX < stave.getX() + partHeaderWidth) {
      console.log('Clicked on stave area:', i);
      selectedPart.value = { ...parts.value[i], partIndex: i };
      menuPosition.value = { x: event.clientX + 8, y: event.clientY + 8 };
      partMenuVisible.value = true;
      menuVisible.value = false; // Hide note menu if open
      clickedStaveArea = true;
      event.stopPropagation();
      break;
    }
  }

  if (clickedStaveArea) return; // Stop if a stave area was clicked

  // Check if an existing note was clicked
  let clickedExistingNote = false;
  for (let i = 0; i < renderedNotesInfo.value.length; i++) {
    const noteInfo = renderedNotesInfo.value[i];
    // Check if click is within the bounding box of a rendered note
    if (
      clickX >= noteInfo.x &&
      clickX <= noteInfo.x + noteInfo.width &&
      clickY >= noteInfo.y &&
      clickY <= noteInfo.y + noteInfo.height
    ) {
      console.log('Clicked on existing note:', noteInfo);
      // Select the note
      selectedNote.value = {
        partIndex: noteInfo.partIndex,
        noteIndex: noteInfo.noteIndex,
        ...parseNotesInput(parts.value[noteInfo.partIndex].notesInput)[noteInfo.noteIndex],
      };
      console.log('Selected Note:', selectedNote.value);

      // Update the dropdowns for the selected part
      const part = parts.value[noteInfo.partIndex];
      part.selectedPitch = selectedNote.value.pitch;
      part.selectedOctave = selectedNote.value.octave;
      part.selectedDuration = selectedNote.value.duration;

      clickedExistingNote = true;
      break;
    }
  }

if (clickedExistingNote) {
// 画面座標でメニュー表示位置を設定
event.stopPropagation();   
 menuPosition.value = { x: event.clientX + 8, y: event.clientY + 8 };
 menuVisible.value  = true;
   return;
} else {
menuVisible.value = false;  
}

  // If no existing note was clicked, proceed to add a new note based on stave and Y-coordinate
  // Find which stave was clicked based on Y-coordinate
  let clickedStaveIndex = -1;
  for (let i = 0; i < vexFlowStaves.value.length; i++) {
    const stave = vexFlowStaves.value[i];
    // VexFlow's getY() is the top line of the stave. getBottomY() is the bottom line.
    if (clickY >= stave.getY() && clickY <= stave.getBottomY()) {
      clickedStaveIndex = i;
      break;
    }
  }

  if (clickedStaveIndex !== -1) {
    console.log(`Clicked on stave at index: ${clickedStaveIndex}`);
    const part = parts.value[clickedStaveIndex];
    const stave = vexFlowStaves.value[clickedStaveIndex];

    // Calculate pitch based on Y-coordinate
    const staveTopY = stave.getYForLine(0); // Y-coordinate of the top line
    const lineSpacing = stave.getSpacingBetweenLines();

    // Calculate the relative Y from the top line of the stave
    const relativeY = clickY - staveTopY;

    // Determine the closest line/space index (0 for top line, 1 for space below, etc.)
    // Each line/space corresponds to half a line spacing
    const closestHalfLineIndex = Math.round(relativeY / (lineSpacing / 2));

    // Map half-line index to pitch and octave (for treble clef)
    // This mapping is simplified and assumes standard treble clef lines
    // 0: E5, 1: D5, 2: C5, 3: B4, 4: A4, 5: G4, 6: F4, 7: E4, 8: D4, 9: C4
    const pitchMap = [
      { pitch: 'E', octave: 5 }, // Line 0
      { pitch: 'D', octave: 5 }, // Space 0-1
      { pitch: 'C', octave: 5 }, // Line 1
      { pitch: 'B', octave: 4 }, // Space 1-2
      { pitch: 'A', octave: 4 }, // Line 2
      { pitch: 'G', octave: 4 }, // Space 2-3
      { pitch: 'F', octave: 4 }, // Line 3
      { pitch: 'E', octave: 4 }, // Space 3-4
      { pitch: 'D', octave: 4 }, // Line 4
      { pitch: 'C', octave: 4 }, // Space 4-5 (below stave)
    ];

    let selectedPitch = 'C';
    let selectedOctave = 4;

    if (closestHalfLineIndex >= 0 && closestHalfLineIndex < pitchMap.length) {
      selectedPitch = pitchMap[closestHalfLineIndex].pitch;
      selectedOctave = pitchMap[closestHalfLineIndex].octave;
    } else {
      console.warn(`Clicked outside standard pitch range for stave. Defaulting to C4.`);
    }

    // For now, just add a quarter note (q)
    const newNote = `${selectedPitch}${selectedOctave}/q`;

    if (part.notesInput) {
      part.notesInput += `, ${newNote}`;
    } else {
      part.notesInput = newNote;
    }
    updateScore(); // Re-render the score with the new note
  }
};

const updateSelectedNote = () => {
  if (!selectedNote.value) return;

  const partIndex = selectedNote.value.partIndex;
  const noteIndex = selectedNote.value.noteIndex;
  const part = parts.value[partIndex];

  const newPitch = part.selectedPitch;
  const newOctave = part.selectedOctave;
  const newDuration = part.selectedDuration;

  const updatedNoteString = `${newPitch}${newOctave}/${newDuration}`;

  const notesArray = parseNotesInput(part.notesInput);
  notesArray[noteIndex] = { ...notesArray[noteIndex], pitch: newPitch, octave: newOctave, duration: newDuration, originalString: updatedNoteString };
  part.notesInput = notesArray.map(note => note.originalString).join(', ');

  selectedNote.value = null; // Deselect the note
  updateScore();
};

const deleteSelectedNote = () => {
  if (!selectedNote.value) return;

  const partIndex = selectedNote.value.partIndex;
  const noteIndex = selectedNote.value.noteIndex;
  const part = parts.value[partIndex];

  const notesArray = parseNotesInput(part.notesInput);
  notesArray.splice(noteIndex, 1);
  part.notesInput = notesArray.map(note => note.originalString).join(', ');

  selectedNote.value = null; // Deselect the note
  updateScore();
};

const drawScore = async () => {
  const container = document.getElementById('score-container');
  if (!container) return;
  container.innerHTML = '';
  console.log(container)
  const factory = new Factory({
    renderer: { elementId: 'score-container', width: 900, height: 400 },
  });

  const score = factory.EasyScore();
  const system = factory.System();

  vexFlowSystem.value = system; // Store the system
  vexFlowStaves.value = []; // Clear previous staves
  vexFlowVoices.value = []; // Clear previous voices

  parts.value.forEach(part => {
    try {
      const vexFlowNotes = score.notes(part.notesInput);
      const voice = score.voice(vexFlowNotes.length > 0 ? vexFlowNotes : score.notes('C4/q, D4/q, E4/q, F4/q'));
      vexFlowVoices.value.push(voice); // Store each voice

      const stave = system.addStave({
        voices: [voice],
      }).addClef('treble').addTimeSignature('4/4');
      vexFlowStaves.value.push(stave); // Store each stave
    } catch (e) {
      console.warn(`Could not parse notes for part ${part.name}: ${e.message}. Using default.`);
      const voice = score.voice(score.notes('C4/q, D4/q, E4/q, F4/q'));
      vexFlowVoices.value.push(voice); // Store each voice
      const stave = system.addStave({
        voices: [voice],
      }).addClef('treble').addTimeSignature('4/4');
      vexFlowStaves.value.push(stave); // Store each stave
    }
  });

  // Format the voices
  new Formatter().joinVoices(vexFlowVoices.value).format(vexFlowVoices.value, 900);
  
  factory.draw();

  // After drawing, collect information about rendered notes
  renderedNotesInfo.value = [];
  vexFlowVoices.value.forEach((voice, voiceIndex) => {
    const rawVoice = toRaw(voice);
    if (rawVoice && typeof rawVoice.getTickables === 'function') {
      rawVoice.getTickables().forEach((note, noteIndex) => {
        if (note.getBoundingBox) {
          const bbox = note.getBoundingBox();
          if (bbox) {
            renderedNotesInfo.value.push({
              partIndex: voiceIndex,
              noteIndex: noteIndex,
              x: bbox.x,
              y: bbox.y,
              width: bbox.w,
              height: bbox.h,
              vexFlowNote: note,
            });
          }
        }
      });
    }
  });

  const canvas = container.querySelector('svg');
  if (canvas) {
    //canvas.style.pointerEvents = 'auto'; // ★ Add this line
    canvas.addEventListener('click', handleClickOnScore);
  }
};

const updateScore = async () => {
  await nextTick();
  await drawScore();
  if (scoreId.value) {
    try {
      const partsData = toRaw(parts.value).map(part => {
        const notes = part.notesInput.split(', ').map((note, index) => {
          const [pitch, duration] = note.split('/');
          return {
            pitch: pitch,
            duration: duration,
            position: index,
          };
        });
        const newPart = {
          name: part.name,
          notes: notes,
        };
        if (typeof part.id === 'number') { // Only include id if it's a valid number
          newPart.id = part.id;
        }
        return newPart;
      });
      console.log('Data being sent to API (updateScore):', partsData); // ここを追加
      await $api.put(`/scores/${scoreId.value}/`, {
        title: 'My Music Sheet',
        parts: partsData,
      });
    } catch (error) {
      console.error('Error updating score:', error);
    }
  }
};

const addPart = () => {
  parts.value.push({ name: `Part ${parts.value.length + 1}`, notesInput: 'C4/q, D4/q, E4/q, F4/q', selectedPitch: 'C', selectedOctave: 4, selectedDuration: 'q' }); // 新しいパートの初期値も4/4拍子を満たすように変更
  updateScore();
};

const updatePartName = () => {
  if (!selectedPart.value) return;
  const partIndex = selectedPart.value.partIndex;
  parts.value[partIndex].name = selectedPart.value.name;
  updateScore();
};

const deleteSelectedPart = () => {
  if (!selectedPart.value) return;
  removePart(selectedPart.value.partIndex);
  partMenuVisible.value = false;
  selectedPart.value = null;
};

const removePart = async (index) => {
  const partToRemove = parts.value[index];
  if (partToRemove.id && scoreId.value) {
    try {
      await $api.delete(`/parts/${partToRemove.id}/`);
      console.log(`Part ${partToRemove.id} deleted from DB.`);
    } catch (error) {
      console.error('Error deleting part from DB:', error);
      // Optionally, you can stop the process if the backend deletion fails
      // return;
    }
  }
  parts.value.splice(index, 1);
  updateScore();
};

const removeLastPart = () => {
  if (parts.value.length > 1) {
    removePart(parts.value.length - 1);
  }
};

onMounted(async () => {
  try {
    const response = await $api.get('/scores/');
    console.log('API GET response:', response.data); // ここを追加
    if (response.data.length > 0) {
      const fetchedScore = response.data[0];
      scoreId.value = fetchedScore.id;
      parts.value = fetchedScore.parts.map(part => {
        const notesInput = part.notes.length < 4
          ? 'C4/q, D4/q, E4/q, F4/q' // Default to a full measure if notes are incomplete
          : part.notes.map(note => `${note.pitch}/${note.duration}`).join(', ');
        return {
          id: part.id,
          name: part.name,
          notesInput: notesInput,
          selectedPitch: 'C', // Add initial values for new dropdowns
          selectedOctave: 4,
          selectedDuration: 'q',
        };
      });
      console.log('Parts after fetching:', parts.value); // ここを追加
    } else {
      const initialPartsData = toRaw(parts.value).map(part => {
        const notes = part.notesInput.split(', ').map((note, index) => {
          const [pitch, duration] = note.split('/');
          return {
            pitch: pitch,
            duration: duration,
            position: index,
          };
        });
        return {
          name: part.name,
          notes: notes,
          selectedPitch: 'C', // Add initial values for new dropdowns
          selectedOctave: 4,
          selectedDuration: 'q',
        };
      });
      console.log('Data being sent to API (onMounted - POST):', initialPartsData); // ここを追加
      const newScore = await $api.post('/scores/', {
        title: 'My Music Sheet',
        parts: initialPartsData,
      });
      scoreId.value = newScore.data.id;
      console.log('New score created:', newScore.data); // ここを追加
    }
  } catch (error) {
    console.error('Error fetching or creating score:', error);
  }
  await updateScore();
});

onMounted(() => {
  window.addEventListener('click', closeMenu);
});
onUnmounted(() => {
  window.removeEventListener('click', closeMenu);
});

function closeMenu() {
  menuVisible.value = false;
  partMenuVisible.value = false;
}

</script>

<style>
.score-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

#score-container {
  width: 100%;
  max-width: 1200px; /* Adjust as needed */
}

.btn-close-white {
  filter: invert(1) grayscale(100%) brightness(200%);
  margin-left: .5em;
}
</style>