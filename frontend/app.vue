<template>
  <div class="container">
    <h1>MusicSheet Editor</h1>
    <div class="row">
      <div class="col-md-6">
        <div v-for="(part, index) in parts" :key="index" class="mb-3">
          <label :for="`part-name-${index}`" class="form-label">Part Name {{ index + 1 }}</label>
          <input type="text" :id="`part-name-${index}`" v-model="part.name" class="form-control mb-2" @input="updateScore" />
          <label :for="`notes-input-${index}`" class="form-label">Notes for {{ part.name }}</label>
          <textarea :id="`notes-input-${index}`" v-model="part.notesInput" @input="updateScore" class="form-control" rows="5"></textarea>
          <button @click="removePart(index)" class="btn btn-danger btn-sm mt-2">Remove Part</button>
        </div>
        <button @click="addPart" class="btn btn-primary mt-3">Add Part</button>
      </div>
      <div class="col-md-6">
        <div ref="scoreContainer"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, toRaw } from 'vue';
import { Factory, Stave, StaveNote, Voice, Formatter } from 'vexflow';

const { $api } = useNuxtApp(); // apiインスタンスをuseNuxtAppから取得

const parts = ref([
  { name: 'Part 1', notesInput: 'C4/q, D4/q, E4/q, F4/q' }, // 初期値を4/4拍子を満たすように変更
]);
const scoreContainer = ref(null);
const scoreId = ref(null);

const drawScore = () => {
  if (!scoreContainer.value) return;
  scoreContainer.value.innerHTML = '';

  const factory = new Factory({
    renderer: { elementId: scoreContainer.value, width: 900, height: 400 },
  });

  const score = factory.EasyScore();
  const system = factory.System();

  parts.value.forEach(part => {
    try {
      const vexFlowNotes = score.notes(part.notesInput);
      const voice = score.voice(vexFlowNotes.length > 0 ? vexFlowNotes : score.notes('C4/q, D4/q, E4/q, F4/q'));

      system.addStave({
        voices: [voice],
      }).addClef('treble').addTimeSignature('4/4');
    } catch (e) {
      console.warn(`Could not parse notes for part ${part.name}: ${e.message}. Using default.`);
      const voice = score.voice(score.notes('C4/q, D4/q, E4/q, F4/q'));
      system.addStave({
        voices: [voice],
      }).addClef('treble').addTimeSignature('4/4');
    }
  });

  factory.draw();
};

const updateScore = async () => {
  drawScore();
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
  parts.value.push({ name: `Part ${parts.value.length + 1}`, notesInput: 'C4/q, D4/q, E4/q, F4/q' }); // 新しいパートの初期値も4/4拍子を満たすように変更
  updateScore();
};

const removePart = async (index) => {
  const partToRemove = parts.value[index];
  if (partToRemove.id && scoreId.value) {
    try {
      await $api.delete(`/parts/${partToRemove.id}/`);
      console.log(`Part ${partToRemove.id} deleted from DB.`);
      parts.value.splice(index, 1);
      updateScore();
    } catch (error) {
      console.error('Error deleting part:', error);
    }
  } else {
    parts.value.splice(index, 1);
    updateScore();
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
  drawScore();
});

</script>

<style>
.container {
  margin-top: 20px;
}
</style>


<style>
.container {
  margin-top: 20px;
}
</style>