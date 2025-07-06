<template>
  <div class="container-fluid mt-3">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1>MusicSheet Editor</h1>
      <div>
        <button @click="addPart" class="btn btn-success me-2">Add New Part</button>
      </div>
    </div>

    <div v-for="(part, index) in parts" :key="part.id || `part-${index}`">
      <MusicPart 
        :part="part" 
        :part-index="index"
        @update:part="handleUpdatePart"
        @delete:part="handleDeletePart"
      />
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, toRaw } from 'vue';
import MusicPart from '~/components/MusicPart.vue';

const { $api } = useNuxtApp();

const parts = ref([]);
const scoreId = ref(null);

const notesInputToMeasures = (input) => {
  if (!input) return [];
  return input.split('|').map((m, idx) => ({
    number: idx + 1,
    notes: m.split(',').map((n, i) => {
      const [pitch, duration, restFlag] = n.trim().split('/');
      return { pitch, duration, rest: restFlag === 'r', position: i };
    })
  }));
};

const fetchScore = async () => {
  try {
    const response = await $api.get('/scores/');
    if (response.data.length > 0) {
      const fetchedScore = response.data[0];
      scoreId.value = fetchedScore.id;
      parts.value = fetchedScore.parts.map(p => ({
        ...p,
        notesInput: p.measures
          .map(m =>
            m.notes
              .map(n => `${n.pitch}/${n.duration}${n.rest ? '/r' : ''}`)
              .join(', ')
          )
          .join(' | ')
      }));
    } else {
      // Create a new score if none exists
      const initialPart = { name: 'Part 1', notesInput: 'C4/q, D4/q, E4/q, F4/q' };
      parts.value = [initialPart];
      await createNewScore();
    }
  } catch (error) {
    console.error('Error fetching score:', error);
  }
};

const createNewScore = async () => {
  try {
    const partsData = toRaw(parts.value).map(part => ({
      name: part.name,
      measures: notesInputToMeasures(part.notesInput)
    }));

    const response = await $api.post('/scores/', { title: 'My Music Sheet', parts: partsData });
    scoreId.value = response.data.id;
    // Update parts with IDs from the server response
    parts.value = response.data.parts.map(p => ({
      ...p,
      notesInput: p.measures
        .map(m => m.notes
          .map(n => `${n.pitch}/${n.duration}${n.rest ? '/r' : ''}`)
          .join(', '))
        .join(' | ')
    }));
  } catch (error) {
    console.error('Error creating new score:', error);
  }
};

const addPart = () => {
  const newPart = { 
    name: `Part ${parts.value.length + 1}`, 
    notesInput: 'C4/q, D4/q, E4/q, F4/q', // Default notes
    notes: [] // Ensure notes array exists
  };
  parts.value.push(newPart);
  updateScore(); // Persist the change
};

const handleUpdatePart = (updatedPart) => {
  const index = parts.value.findIndex(p => p.id === updatedPart.id);
  if (index !== -1) {
    parts.value[index] = updatedPart;
    updateScore();
  }
};

const handleDeletePart = (index) => {
  parts.value.splice(index, 1);
  updateScore();
};

const updateScore = async () => {
  if (!scoreId.value) return;
  try {
    const partsData = toRaw(parts.value).map(part => ({
      id: part.id,
      name: part.name,
      measures: notesInputToMeasures(part.notesInput)
    }));
    await $api.put(`/scores/${scoreId.value}/`, { title: 'My Music Sheet', parts: partsData });
  } catch (error) {
    console.error('Error updating score:', error);
  }
};

onMounted(fetchScore);

</script>

<style>
body {
  background-color: #f8f9fa;
}
</style>