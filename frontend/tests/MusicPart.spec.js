import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import MusicPart from '../components/MusicPart.vue'

vi.mock('vexflow', () => {
  class MockSystem {
    addStave() { return this }
    addClef() { return this }
    addTimeSignature() { return this }
  }
  class MockFactory {
    EasyScore() {
      return {
        notes: () => [],
        voice: () => ({ getTickables: () => [] })
      }
    }
    System() { return new MockSystem() }
    draw() {}
  }
  return { Factory: MockFactory, Formatter: {}, StaveNote: class {} }
})

describe('MusicPart.vue', () => {
  const baseProps = { part: { name: 'Test Part', notesInput: '' }, partIndex: 0 }

  it('renders part name', () => {
    const wrapper = mount(MusicPart, { props: baseProps })
    expect(wrapper.find('h5').text()).toBe('Test Part')
  })

  it('emits update event when part name edited', async () => {
    const wrapper = mount(MusicPart, { props: baseProps })
    await wrapper.find('button.btn-primary').trigger('click')
    await nextTick()
    const input = wrapper.find('input.form-control')
    await input.setValue('New Name')
    expect(wrapper.emitted()['update:part']).toBeTruthy()
    expect(wrapper.emitted()['update:part'][0][0].name).toBe('New Name')
  })

  it('updates selected note and emits changed notes', () => {
    const wrapper = mount(MusicPart, {
      props: { part: { name: 'Test Part', notesInput: 'C4/q, D4/q, E4/q, F4/q' }, partIndex: 0 }
    })

    wrapper.vm.selectedNote = { pitch: 'G', octave: 4, duration: 'q', noteIndex: 1 }
    wrapper.vm.updateSelectedNote()

    const emitted = wrapper.emitted()['update:part']?.[0]?.[0]
    expect(emitted).toBeTruthy()
    expect(emitted.notesInput).toBe('C4/q, G4/q, E4/q, F4/q')
  })

  it('updates note duration to eighth and fills rest', () => {
    const wrapper = mount(MusicPart, {
      props: { part: { name: 'Test Part', notesInput: 'C4/q, D4/q, E4/q, F4/q' }, partIndex: 0 }
    })

    wrapper.vm.selectedNote = { pitch: 'D', octave: 4, duration: '8', noteIndex: 1 }
    wrapper.vm.updateSelectedNote()

    const emitted = wrapper.emitted()['update:part']?.[0]?.[0]
    expect(emitted).toBeTruthy()
    expect(emitted.notesInput).toBe('C4/q, D4/8, E4/q, F4/q, B4/8/r')
  })

  it('updates note duration to sixteenth and fills rest', () => {
    const wrapper = mount(MusicPart, {
      props: { part: { name: 'Test Part', notesInput: 'C4/q, D4/q, E4/q, F4/q' }, partIndex: 0 }
    })

    wrapper.vm.selectedNote = { pitch: 'D', octave: 4, duration: '16', noteIndex: 1 }
    wrapper.vm.updateSelectedNote()

    const emitted = wrapper.emitted()['update:part']?.[0]?.[0]
    expect(emitted).toBeTruthy()
    expect(emitted.notesInput).toBe('C4/q, D4/16, E4/q, F4/q, B4/8/r, B4/16/r')
  })

  it('changes a note to a rest', () => {
    const wrapper = mount(MusicPart, {
      props: { part: { name: 'Test Part', notesInput: 'C4/q, D4/q, E4/q' }, partIndex: 0 }
    })

    wrapper.vm.selectedNote = { pitch: 'B', octave: 4, duration: 'q', rest: true, noteIndex: 1 }
    wrapper.vm.updateSelectedNote()

    const emitted = wrapper.emitted()['update:part']?.[0]?.[0]
    expect(emitted).toBeTruthy()
    expect(emitted.notesInput).toBe('C4/q, B4/q/r, E4/q, B4/q/r')
  })

  it('changes a rest to a note', () => {
    const wrapper = mount(MusicPart, {
      props: { part: { name: 'Test Part', notesInput: 'C4/q, B4/q/r, E4/q' }, partIndex: 0 }
    })

    wrapper.vm.selectedNote = { pitch: 'D', octave: 4, duration: 'q', rest: false, noteIndex: 1 }
    wrapper.vm.updateSelectedNote()

    const emitted = wrapper.emitted()['update:part']?.[0]?.[0]
    expect(emitted).toBeTruthy()
    expect(emitted.notesInput).toBe('C4/q, D4/q, E4/q, B4/q/r')
  })

  it('deletes selected note and emits changed notes', () => {
    const wrapper = mount(MusicPart, {
      props: { part: { name: 'Test Part', notesInput: 'C4/q, D4/q, E4/q' }, partIndex: 0 }
    })

    wrapper.vm.selectedNote = { noteIndex: 0 }
    wrapper.vm.deleteSelectedNote()

    const emitted = wrapper.emitted()['update:part']?.[0]?.[0]
    expect(emitted).toBeTruthy()
    expect(emitted.notesInput).toBe('D4/q, E4/q, B4/h/r')
  })
})
