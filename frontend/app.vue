<template>
  <div class="container">
    <h1>MusicSheet Editor</h1>
    <div class="row">
      <div class="col-md-6">
        <textarea v-model="notesInput" @input="updateScore" class="form-control" rows="10"></textarea>
      </div>
      <div class="col-md-6">
        <div ref="scoreContainer"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Factory, Stave, StaveNote, Voice, Formatter } from 'vexflow';

const notesInput = ref('C4/q, D4/q, E4/q, F4/q');
const scoreContainer = ref(null);

const drawScore = () => {
  if (!scoreContainer.value) return;
  scoreContainer.value.innerHTML = '';

  const factory = new Factory({
    renderer: { elementId: scoreContainer.value, width: 500, height: 200 },
  });

  const score = factory.EasyScore();
  const system = factory.System();

  system.addStave({
    voices: [score.voice(score.notes(notesInput.value))],
  }).addClef('treble').addTimeSignature('4/4');

  factory.draw();
};

const updateScore = () => {
  drawScore();
};

onMounted(() => {
  drawScore();
});
</script>

<style>
.container {
  margin-top: 20px;
}
</style>
