// Caméra orthographique en vue de dessus (plan 2D) avec pan + zoom.
// La rotation est volontairement désactivée pour rester en 2D.
// Le frustum de base (left/right/top/bottom, géré par main.js au resize)
// n'est jamais modifié : le zoom utilise camera.zoom, le pan déplace
// la position de la caméra.
import * as THREE from 'three';

export class OrthoTopControls {
  constructor(camera, domElement) {
    this.camera = camera;
    this.domElement = domElement;

    this.target = new THREE.Vector3(0, 0, 0); // point du sol sous la caméra
    this.zoom = 1;
    this.minZoom = 0.35;
    this.maxZoom = 8;

    this.minPanX = -60;
    this.maxPanX = 60;
    this.minPanZ = -60;
    this.maxPanZ = 60;

    this.enabled = true;
    this.needsUpdate = true;

    this._panning = false;
    this._lastPointer = { x: 0, y: 0 };
    this._pointers = new Map();
    this._pinchStart = 0;
    this._pinchStartZoom = 1;

    this._onPointerDown = (e) => this._handlePointerDown(e);
    this._onPointerMove = (e) => this._handlePointerMove(e);
    this._onPointerUp = (e) => this._handlePointerUp(e);
    this._onWheel = (e) => this._handleWheel(e);
    this._onContextMenu = (e) => e.preventDefault();

    domElement.addEventListener('pointerdown', this._onPointerDown);
    domElement.addEventListener('pointermove', this._onPointerMove);
    domElement.addEventListener('pointerup', this._onPointerUp);
    domElement.addEventListener('pointercancel', this._onPointerUp);
    domElement.addEventListener('wheel', this._onWheel, { passive: false });
    domElement.addEventListener('contextmenu', this._onContextMenu);
  }

  dispose() {
    const d = this.domElement;
    d.removeEventListener('pointerdown', this._onPointerDown);
    d.removeEventListener('pointermove', this._onPointerMove);
    d.removeEventListener('pointerup', this._onPointerUp);
    d.removeEventListener('pointercancel', this._onPointerUp);
    d.removeEventListener('wheel', this._onWheel);
    d.removeEventListener('contextmenu', this._onContextMenu);
  }

  _handlePointerDown(e) {
    if (!this.enabled) return;
    this._pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (this._pointers.size === 1) {
      this._panning = true;
      this._lastPointer = { x: e.clientX, y: e.clientY };
      this.domElement.setPointerCapture(e.pointerId);
    } else if (this._pointers.size === 2) {
      this._pinchStart = this._pinchDistance();
      this._pinchStartZoom = this.zoom;
    }
  }

  _handlePointerMove(e) {
    if (!this.enabled || !this._pointers.has(e.pointerId)) return;
    this._pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });

    if (this._pointers.size >= 2) {
      const dist = this._pinchDistance();
      if (this._pinchStart > 0 && dist > 0) {
        this._setZoom(this._pinchStartZoom * (dist / this._pinchStart));
        this.needsUpdate = true;
      }
      return;
    }
    if (!this._panning) return;

    const dx = e.clientX - this._lastPointer.x;
    const dy = e.clientY - this._lastPointer.y;
    this._lastPointer = { x: e.clientX, y: e.clientY };

    // Le contenu suit le pointeur (sens "carte") :
    // glisser à droite → la caméra part à gauche.
    const wpp = this._worldPerPixel();
    this.target.x -= dx * wpp;
    this.target.z -= dy * wpp;
    this._clampTarget();
    this.needsUpdate = true;
  }

  _handlePointerUp(e) {
    this._pointers.delete(e.pointerId);
    if (this._pointers.size === 0) this._panning = false;
    if (this._pointers.size < 2) this._pinchStart = 0;
  }

  _handleWheel(e) {
    if (!this.enabled) return;
    e.preventDefault();
    // Zoom vers le curseur : le point monde sous la souris reste immobile.
    const rect = this.domElement.getBoundingClientRect();
    const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    const ny = -(((e.clientY - rect.top) / rect.height) * 2 - 1);

    const before = this._screenToWorld(nx, ny);
    const factor = Math.exp(-e.deltaY * 0.0012);
    this._setZoom(this.zoom * factor);

    const after = this._screenToWorld(nx, ny);
    this.target.x += before.x - after.x;
    this.target.z += before.z - after.z;
    this._clampTarget();
    this.needsUpdate = true;
  }

  _pinchDistance() {
    const pts = [...this._pointers.values()];
    if (pts.length < 2) return 0;
    return Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
  }

  _setZoom(z) {
    this.zoom = Math.min(this.maxZoom, Math.max(this.minZoom, z));
  }

  _clampTarget() {
    this.target.x = Math.min(this.maxPanX, Math.max(this.minPanX, this.target.x));
    this.target.z = Math.min(this.maxPanZ, Math.max(this.minPanZ, this.target.z));
  }

  _halfW() {
    return (this.camera.right - this.camera.left) / 2 / this.camera.zoom;
  }

  _halfH() {
    return (this.camera.top - this.camera.bottom) / 2 / this.camera.zoom;
  }

  _worldPerPixel() {
    return (this.camera.right - this.camera.left) / this.domElement.clientWidth / this.camera.zoom;
  }

  _screenToWorld(nx, ny) {
    // Vue de dessus, up = -z : x écran → +x monde, y écran haut → -z monde.
    return {
      x: this.target.x + nx * this._halfW(),
      z: this.target.z - ny * this._halfH(),
    };
  }

  update() {
    const c = this.camera;
    c.zoom = this.zoom;
    c.position.set(this.target.x, 100, this.target.z);
    c.up.set(0, 0, -1); // nord (-z) en haut de l'écran
    c.lookAt(this.target.x, 0, this.target.z);
    c.updateProjectionMatrix();
    this.needsUpdate = false;
  }
}
