import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { prepare, layout } from '@chenglou/pretext';
export async function initMap() {

/* ═══════════════════════════════════════════════════════════
   GLOBAL STATE & ASSET LOAD
   ═══════════════════════════════════════════════════════════ */
let DATA = { kpi: { samples: 869, critical: 22, high: 323, low: 515 }, priority: [], details: {} };
let RIVERS = { ganga_main: [], tributaries: {} };
let DISTRICT_CENTROIDS = {};
let NATIONAL_STATS = {};
let INDIA_STATES = { features: [] };

try {
  const isStaticHost = window.location.port !== '8000';
  const dataFetchPromise = isStaticHost
    ? fetch('data.json').then(r => r.json()).catch(() => ({}))
    : fetch('/api/dashboard-data').then(r => r.ok ? r.json() : fetch('data.json').then(res => res.json())).catch(() => fetch('data.json').then(res => res.json()));

  const [rData, rRivers, rCentroids, rStats, rStates] = await Promise.all([
    dataFetchPromise,
    fetch('assets/rivers_ganga_basin.json').then(r => r.json()).catch(() => ({ ganga_main: [], tributaries: {} })),
    fetch('assets/district_centroids.json').then(r => r.json()).catch(() => ({})),
    fetch('assets/national_state_stats.json').then(r => r.json()).catch(() => ({})),
    fetch('assets/india_states_compact.geojson').then(r => r.json()).catch(() => ({ features: [] }))
  ]);
  if (rData.priority) {
    DATA = rData;
    window.dispatchEvent(new CustomEvent("triage-data-loaded", { detail: DATA }));
    const nf = new Intl.NumberFormat('en-IN');
    if (DATA.kpi) {
      const elTotal = document.getElementById('kpi-total');
      const elCrit = document.getElementById('kpi-crit');
      const elHigh = document.getElementById('kpi-high');
      const elLow = document.getElementById('kpi-low');
      const elStatChip = document.getElementById('stat-chip');

      if (elTotal && DATA.kpi.samples !== undefined) elTotal.textContent = nf.format(DATA.kpi.samples);
      if (elCrit && DATA.kpi.critical !== undefined) elCrit.textContent = nf.format(DATA.kpi.critical);
      if (elHigh && DATA.kpi.high !== undefined) elHigh.textContent = nf.format(DATA.kpi.high);
      if (elLow && DATA.kpi.low !== undefined) elLow.textContent = nf.format(DATA.kpi.low);
      if (elStatChip && DATA.kpi.samples !== undefined) {
        elStatChip.textContent = `${nf.format(DATA.kpi.samples)} Samples · ${nf.format(100690)} Historical`;
      }
    }
  }
  if (rRivers.ganga_main) RIVERS = rRivers;
  if (rCentroids) DISTRICT_CENTROIDS = rCentroids;
  if (rStats) NATIONAL_STATS = rStats;
  if (rStates.features) INDIA_STATES = rStates;
} catch (err) {
  console.warn('Asset loading notice:', err);
}

/* ═══════════════════════════════════════════════════════════
   THREE.JS SCENE SETUP
   ═══════════════════════════════════════════════════════════ */
const canvas = document.getElementById('webgl');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x070d19);
scene.fog = new THREE.FogExp2(0x070d19, 0.0035);

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, preserveDrawingBuffer: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.25;

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.maxDistance = 300;
controls.minDistance = 15;

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
scene.add(ambientLight);

const sunLight = new THREE.DirectionalLight(0xffffff, 1.8);
sunLight.position.set(100, 80, 100);
scene.add(sunLight);

const blueRimLight = new THREE.DirectionalLight(0x06b6d4, 1.2);
blueRimLight.position.set(-100, -50, -80);
scene.add(blueRimLight);

/* ═══════════════════════════════════════════════════════════
   MODES & GROUPS
   ═══════════════════════════════════════════════════════════ */
let CURRENT_MODE = 'globe'; // 'globe' or 'regional'
const globeGroup = new THREE.Group();
const regionalGroup = new THREE.Group();
scene.add(globeGroup);
scene.add(regionalGroup);

regionalGroup.visible = false;

/* ═══════════════════════════════════════════════════════════
   1. 3D EARTH GLOBE CREATION (With Atmosphere & India Centered)
   ═══════════════════════════════════════════════════════════ */
const GLOBE_RADIUS = 35;

// Earth Surface
const textureLoader = new THREE.TextureLoader();
const earthTexture = textureLoader.load(
  'https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg',
  () => renderer.render(scene, camera)
);

const earthGeo = new THREE.SphereGeometry(GLOBE_RADIUS, 64, 64);
const earthMat = new THREE.MeshStandardMaterial({
  map: earthTexture,
  roughness: 0.7,
  metalness: 0.1,
});
const earthMesh = new THREE.Mesh(earthGeo, earthMat);
globeGroup.add(earthMesh);

// Atmosphere Glow
const atmoGeo = new THREE.SphereGeometry(GLOBE_RADIUS * 1.025, 64, 64);
const atmoMat = new THREE.ShaderMaterial({
  vertexShader: `
    varying vec3 vNormal;
    void main() {
      vNormal = normalize(normalMatrix * normal);
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: `
    varying vec3 vNormal;
    void main() {
      float intensity = pow(0.72 - dot(vNormal, vec3(0, 0, 1.0)), 2.2);
      gl_FragColor = vec4(0.02, 0.71, 0.83, 1.0) * intensity;
    }
  `,
  blending: THREE.AdditiveBlending,
  side: THREE.BackSide,
  transparent: true
});
const atmoMesh = new THREE.Mesh(atmoGeo, atmoMat);
globeGroup.add(atmoMesh);

// Starfield Background
const starGeo = new THREE.BufferGeometry();
const starCount = 1200;
const starPos = new Float32Array(starCount * 3);
for (let i = 0; i < starCount * 3; i++) {
  starPos[i] = (Math.random() - 0.5) * 600;
}
starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
const starMat = new THREE.PointsMaterial({ color: 0x94a3b8, size: 0.8, transparent: true, opacity: 0.6 });
scene.add(new THREE.Points(starGeo, starMat));

// Convert Lat/Lon to 3D Sphere Coordinates
function latLonToVector3(lat, lon, radius) {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -(radius * Math.sin(phi) * Math.cos(theta)),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}

// Initial India Facing Orientation (Center of India is ~22°N, 82°E)
const indiaCenter = latLonToVector3(22.5, 82.5, GLOBE_RADIUS);
camera.position.set(indiaCenter.x * 2.3, indiaCenter.y * 1.8 + 15, indiaCenter.z * 2.3);
controls.target.copy(new THREE.Vector3(0, 0, 0));

// Add Glowing River Paths on Globe
const globeRiversGroup = new THREE.Group();
globeGroup.add(globeRiversGroup);

function buildGlobeRivers() {
  const riverMat = new THREE.LineBasicMaterial({
    color: 0x38bdf8,
    transparent: true,
    opacity: 0.9,
    linewidth: 2
  });

  // Ganga Stem
  if (RIVERS.ganga_main) {
    RIVERS.ganga_main.forEach(line => {
      const pts = line.map(p => latLonToVector3(p[1], p[0], GLOBE_RADIUS * 1.004));
      const geom = new THREE.BufferGeometry().setFromPoints(pts);
      globeRiversGroup.add(new THREE.Line(geom, riverMat));
    });
  }

  // Tributaries
  if (RIVERS.tributaries) {
    Object.values(RIVERS.tributaries).forEach(coords => {
      const pts = coords.map(p => latLonToVector3(p[1], p[0], GLOBE_RADIUS * 1.004));
      const geom = new THREE.BufferGeometry().setFromPoints(pts);
      globeRiversGroup.add(new THREE.Line(geom, riverMat));
    });
  }
}
buildGlobeRivers();

// Add Indian State Outlines on Globe
const globeStatesGroup = new THREE.Group();
globeGroup.add(globeStatesGroup);

function buildGlobeStates() {
  const stateMat = new THREE.LineBasicMaterial({
    color: 0x0ea5e9,
    transparent: true,
    opacity: 0.55,
    linewidth: 1
  });

  if (INDIA_STATES.features) {
    INDIA_STATES.features.forEach(feat => {
      const g = feat.geometry;
      if (!g) return;
      const rings = g.type === 'Polygon' ? g.coordinates : g.type === 'MultiPolygon' ? g.coordinates.flat() : [];
      rings.forEach(ring => {
        const pts = ring.map(p => latLonToVector3(p[1], p[0], GLOBE_RADIUS * 1.002));
        const geom = new THREE.BufferGeometry().setFromPoints(pts);
        globeStatesGroup.add(new THREE.Line(geom, stateMat));
      });
    });
  }
}
buildGlobeStates();

/* ═══════════════════════════════════════════════════════════
   2. REGIONAL INDO-GANGETIC BASIN (UP & Bihar) 3D MAP
   ═══════════════════════════════════════════════════════════ */
// Projection helper: Map lat/lon to flat X/Z plane centered around UP & Bihar
// UP+Bihar bounds: Lat 23.8 to 30.5, Lon 77.0 to 88.2
function latLonToPlane(lat, lon) {
  const centerLat = 26.5;
  const centerLon = 82.5;
  const scale = 8.5; // units per degree
  const x = (lon - centerLon) * scale;
  const z = -(lat - centerLat) * scale;
  return { x, z };
}

// Terrain baseplate for UP and Bihar
const baseGeo = new THREE.PlaneGeometry(116, 70, 32, 32);
const baseMat = new THREE.MeshStandardMaterial({
  color: 0x091424,
  roughness: 0.85,
  metalness: 0.2,
  transparent: true,
  opacity: 0.95
});
const baseMesh = new THREE.Mesh(baseGeo, baseMat);
baseMesh.rotation.x = -Math.PI / 2;
baseMesh.position.y = -0.1;
regionalGroup.add(baseMesh);

// Subtle Tactical Grid lines
const regionalGrid = new THREE.GridHelper(124, 44, 0x1e3a8a, 0x0e1c38);
regionalGrid.position.y = -0.09;
regionalGroup.add(regionalGrid);

// ═══════════════════════════════════════════════════════════
// REGIONAL STATE BORDERS & 3D BILLBOARD LABELS (UP & Bihar)
// ═══════════════════════════════════════════════════════════
const regionalStatesGroup = new THREE.Group();
regionalGroup.add(regionalStatesGroup);

function makeStateLabelSprite(title, sub) {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 120;
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = 'rgba(10, 20, 38, 0.78)';
  ctx.strokeStyle = 'rgba(56, 189, 248, 0.45)';
  ctx.lineWidth = 2.5;
  
  const x = 4, y = 4, w = 504, h = 112, r = 16;
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  ctx.font = 'bold 28px Inter, system-ui, sans-serif';
  ctx.fillStyle = '#e2e8f0';
  ctx.textAlign = 'center';
  ctx.fillText(title, 256, 50);

  if (sub) {
    ctx.font = '500 17px Inter, system-ui, sans-serif';
    ctx.fillStyle = '#64748b';
    ctx.fillText(sub, 256, 86);
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.LinearFilter;
  const spriteMat = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthTest: false
  });
  const sprite = new THREE.Sprite(spriteMat);
  sprite.scale.set(9.5, 2.2, 1);
  return sprite;
}

function buildRegionalStateBorders() {
  const upBiharMat = new THREE.LineBasicMaterial({
    color: 0x38bdf8,
    transparent: true,
    opacity: 0.65,
    linewidth: 1
  });
  const neighborMat = new THREE.LineBasicMaterial({
    color: 0x1e3a8a,
    transparent: true,
    opacity: 0.3,
    linewidth: 1
  });

  if (INDIA_STATES.features) {
    INDIA_STATES.features.forEach(feat => {
      const g = feat.geometry;
      if (!g) return;
      const name = (feat.properties && feat.properties.NAME_1) || '';
      const isCore = (name === 'Uttar Pradesh' || name === 'Bihar');
      const isNeighbor = ['Jharkhand', 'West Bengal', 'Madhya Pradesh', 'Haryana', 'Uttaranchal'].includes(name);
      if (!isCore && !isNeighbor) return;

      const mat = isCore ? upBiharMat : neighborMat;
      const rings = g.type === 'Polygon' ? g.coordinates : g.type === 'MultiPolygon' ? g.coordinates.flat() : [];
      rings.forEach(ring => {
        const pts = ring.map(p => {
          const { x, z } = latLonToPlane(p[1], p[0]);
          return new THREE.Vector3(x, 0.04, z);
        });
        const geom = new THREE.BufferGeometry().setFromPoints(pts);
        regionalStatesGroup.add(new THREE.Line(geom, mat));
      });
    });
  }

  // 3D Billboard Labels for Uttar Pradesh & Bihar
  const upLabel = makeStateLabelSprite('UTTAR PRADESH', '75 Districts · Upper/Middle Basin');
  const upPos = latLonToPlane(27.4, 80.6);
  upLabel.position.set(upPos.x, 1.4, upPos.z);
  regionalStatesGroup.add(upLabel);

  const biharLabel = makeStateLabelSprite('BIHAR', '38 Districts · Lower Gangetic Plain');
  const biharPos = latLonToPlane(25.8, 85.8);
  biharLabel.position.set(biharPos.x, 1.4, biharPos.z);
  regionalStatesGroup.add(biharLabel);
}
buildRegionalStateBorders();

// ═══════════════════════════════════════════════════════════
// REGIONAL HYDROLOGICAL RIVER NETWORK (Wide Glowing 3D Ribbons)
// ═══════════════════════════════════════════════════════════
const regionalRiversGroup = new THREE.Group();
regionalGroup.add(regionalRiversGroup);

// River Ribbon Quad-Strip Geometry Generator
function createRiverRibbonGeometry(rawPoints, width) {
  const geom = new THREE.BufferGeometry();
  if (!rawPoints || rawPoints.length < 2) return geom;

  // Deduplicate adjacent points
  const points = [rawPoints[0]];
  for (let i = 1; i < rawPoints.length; i++) {
    if (rawPoints[i].distanceToSquared(points[points.length - 1]) > 0.0001) {
      points.push(rawPoints[i]);
    }
  }
  const numPts = points.length;
  if (numPts < 2) return geom;

  const positions = new Float32Array(numPts * 2 * 3);
  const uvs = new Float32Array(numPts * 2 * 2);
  const indices = [];
  const halfWidth = width / 2;

  for (let i = 0; i < numPts; i++) {
    const curr = points[i];
    let dir = new THREE.Vector3();
    if (i === 0) {
      dir.subVectors(points[1], curr);
    } else if (i === numPts - 1) {
      dir.subVectors(curr, points[i - 1]);
    } else {
      const d1 = new THREE.Vector3().subVectors(curr, points[i - 1]).normalize();
      const d2 = new THREE.Vector3().subVectors(points[i + 1], curr).normalize();
      dir.addVectors(d1, d2);
    }
    dir.y = 0;
    if (dir.lengthSq() < 0.00001) dir.set(1, 0, 0);
    dir.normalize();

    // Normal in XZ plane
    const norm = new THREE.Vector3(-dir.z, 0, dir.x);

    const left = new THREE.Vector3().copy(curr).addScaledVector(norm, halfWidth);
    const right = new THREE.Vector3().copy(curr).addScaledVector(norm, -halfWidth);

    const vIdx = i * 2;
    positions[vIdx * 3]     = left.x;
    positions[vIdx * 3 + 1] = left.y;
    positions[vIdx * 3 + 2] = left.z;

    positions[(vIdx + 1) * 3]     = right.x;
    positions[(vIdx + 1) * 3 + 1] = right.y;
    positions[(vIdx + 1) * 3 + 2] = right.z;

    const u = i / (numPts - 1);
    uvs[vIdx * 2]     = u;
    uvs[vIdx * 2 + 1] = 0;
    uvs[(vIdx + 1) * 2]     = u;
    uvs[(vIdx + 1) * 2 + 1] = 1;

    if (i < numPts - 1) {
      const a = vIdx;
      const b = vIdx + 1;
      const c = vIdx + 2;
      const d = vIdx + 3;
      indices.push(a, b, c);
      indices.push(b, d, c);
    }
  }

  geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geom.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
  geom.setIndex(indices);
  geom.computeVertexNormals();
  return geom;
}

function makeRiverLabelSprite(name, sub, isMain = false) {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 120;
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = isMain ? 'rgba(6, 182, 212, 0.25)' : 'rgba(10, 25, 47, 0.85)';
  ctx.strokeStyle = isMain ? 'rgba(6, 182, 212, 0.95)' : 'rgba(56, 189, 248, 0.7)';
  ctx.lineWidth = isMain ? 3 : 2;

  const x = 4, y = 4, w = 504, h = 112, r = 16;
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  ctx.font = isMain ? 'bold 30px Inter, system-ui, sans-serif' : 'bold 26px Inter, system-ui, sans-serif';
  ctx.fillStyle = isMain ? '#38bdf8' : '#7dd3fc';
  ctx.textAlign = 'center';
  ctx.fillText(name, 256, 50);

  if (sub) {
    ctx.font = '500 17px Inter, system-ui, sans-serif';
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(sub, 256, 86);
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.LinearFilter;
  const spriteMat = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthTest: false
  });
  const sprite = new THREE.Sprite(spriteMat);
  sprite.scale.set(isMain ? 8.2 : 7.0, isMain ? 1.9 : 1.6, 1);
  return sprite;
}

// Corridor Telemetry & Hydrological Metadata
const RIVER_DATA = {
  all: {
    name: 'Indo-Gangetic Basin Alluvial System',
    length: '7 Major Corridors · 1,359 Stations',
    stations: '1,359 Tested',
    crit: '22 Critical',
    meanScore: '11.8 / 100',
    primaryHazard: 'Turbidity / Iron',
    badge: 'Indo-Gangetic',
    overview: 'High geogenic iron along Kosi &amp; Gomti floodplains, arsenic concentration in middle Ganga (Ballia/Buxar), and fluoride in Son interfluve.',
    cam: { x: 0, y: 52, z: 58, tx: 0, ty: 0, tz: 0 }
  },
  ganga_main: {
    name: 'Ganga Main Stem',
    length: '2,525 km (Devprayag to Bay of Bengal)',
    stations: '255 Stations',
    crit: '4 Critical',
    meanScore: '18.4 / 100',
    primaryHazard: 'Arsenic (As) &amp; Fecal Coliform',
    badge: 'Basin Artery',
    overview: 'Middle Gangetic aquifer plume across Ballia–Buxar–Varanasi belt exceeding BIS IS 10500 permissible limits. High seasonal coliform load.',
    districts: ['Varanasi', 'Kanpur Nagar', 'Prayagraj', 'Ballia', 'Buxar', 'Patna', 'Bhagalpur', 'Mirzapur', 'Ghazipur', 'Vaishali', 'Samastipur', 'Begusarai', 'Munger', 'Katihar', 'Budaun', 'Farrukhabad', 'Kannauj', 'Unnao', 'Fatehpur', 'Chandauli'],
    labelPos: { lat: 25.5, lon: 83.5, sub: '2,525 km · Basin Artery' },
    cam: { x: 10, y: 32, z: 28, tx: 8, ty: 0, tz: 4 },
    centerPos: latLonToPlane(25.5, 83.5)
  },
  Yamuna: {
    name: 'Yamuna Corridor',
    length: '1,376 km (Yamunotri to Prayagraj)',
    stations: '106 Stations',
    crit: '2 Critical',
    meanScore: '20.1 / 100',
    primaryHazard: 'TDS / Salinity &amp; Fluoride',
    badge: 'SW Tributary',
    overview: 'Semi-arid interfluve with elevated groundwater salinity and localized fluoride dissolution in Agra, Mathura, and Etawah zones.',
    districts: ['Agra', 'Mathura', 'Firozabad', 'Etawah', 'Auraiya', 'Jalaun', 'Hamirpur', 'Banda', 'Baghpat', 'Ghaziabad', 'Gautam Buddha Nagar', 'Saharanpur', 'Shamli', 'Muzaffarnagar', 'Etah', 'Kaushambi'],
    labelPos: { lat: 27.2, lon: 78.2, sub: '1,376 km · SW Tributary' },
    cam: { x: -28, y: 28, z: 22, tx: -26, ty: 0, tz: -4 },
    centerPos: latLonToPlane(27.2, 78.2)
  },
  Gomti: {
    name: 'Gomti Catchment',
    length: '960 km (Pilibhit to Ghazipur Confluence)',
    stations: '193 Stations',
    crit: '10 Critical',
    meanScore: '14.2 / 100',
    primaryHazard: 'Iron &amp; Domestic Nitrates',
    badge: 'Central UP',
    overview: 'Groundwater-fed alluvial stream draining central UP. Heavy domestic nutrient runoff in Lucknow/Sitapur with shallow aquifer iron leaching.',
    districts: ['Lucknow', 'Jaunpur', 'Sultanpur', 'Sitapur', 'Lakhimpur Kheri', 'Bara Banki', 'Amethi', 'Pilibhit', 'Hardoi', 'Shahjahanpur', 'Kheri'],
    labelPos: { lat: 26.85, lon: 80.95, sub: '960 km · Central UP' },
    cam: { x: -10, y: 26, z: 16, tx: -10, ty: 0, tz: -6 },
    centerPos: latLonToPlane(26.85, 80.95)
  },
  Ghaghara: {
    name: 'Ghaghara Basin (Karnali)',
    length: '1,080 km (Tibetan Plateau to Saran)',
    stations: '113 Stations',
    crit: '0 Critical',
    meanScore: '13.3 / 100',
    primaryHazard: 'Monsoon Turbidity &amp; pH',
    badge: 'High Discharge',
    overview: 'Massive Himalayan snowmelt sediment load with rapid monsoon overbank flooding. Elevated turbidity and localized alkaline groundwater.',
    districts: ['Ayodhya', 'Faizabad', 'Gorakhpur', 'Deoria', 'Barabanki', 'Bahraich', 'Gonda', 'Basti', 'Mau', 'Ballia', 'Saran', 'Siwan', 'Ambedkar Nagar'],
    labelPos: { lat: 26.8, lon: 82.3, sub: '1,080 km · High Discharge' },
    cam: { x: 2, y: 28, z: 14, tx: 2, ty: 0, tz: -8 },
    centerPos: latLonToPlane(26.8, 82.3)
  },
  Gandak: {
    name: 'Gandak Zone (Narayani)',
    length: '630 km (Nepal to Sonpur/Patna Confluence)',
    stations: '168 Stations',
    crit: '0 Critical',
    meanScore: '14.6 / 100',
    primaryHazard: 'Agrochemicals &amp; Arsenic',
    badge: 'Himalayan Runoff',
    overview: 'Steep piedmont alluvial fans in Champaran &amp; Muzaffarpur. Intensive fertilizer percolation combined with reducing alluvial aquifer conditions.',
    districts: ['Pashchim Champaran', 'Purbi Champaran', 'Gopalganj', 'Saran', 'Muzaffarpur', 'Vaishali', 'Sitamarhi', 'Sheohar'],
    labelPos: { lat: 26.6, lon: 85.0, sub: '630 km · Himalayan Runoff' },
    cam: { x: 18, y: 26, z: 14, tx: 18, ty: 0, tz: -6 },
    centerPos: latLonToPlane(26.6, 85.0)
  },
  Kosi: {
    name: 'Kosi Floodplain (Saptakoshi)',
    length: '729 km (Nepal to Kursela Confluence)',
    stations: '95 Stations',
    crit: '4 Critical',
    meanScore: '20.8 / 100',
    primaryHazard: 'Severe Geogenic Iron (&gt;3 mg/L)',
    badge: 'Braided Plain',
    overview: 'Dynamic braided megafan with shifting channels. Highly anoxic shallow aquifers trigger extreme geogenic iron mobilization across Saharsa/Supaul.',
    districts: ['Supaul', 'Saharsa', 'Madhepura', 'Khagaria', 'Katihar', 'Purnia', 'Araria', 'Kishanganj', 'Darbhanga', 'Madhubani'],
    labelPos: { lat: 25.9, lon: 87.0, sub: '729 km · High Geogenic Iron' },
    cam: { x: 32, y: 26, z: 18, tx: 32, ty: 0, tz: -2 },
    centerPos: latLonToPlane(25.9, 87.0)
  },
  Son: {
    name: 'Son Interfluve',
    length: '784 km (Amarkantak to Patna Confluence)',
    stations: '214 Stations',
    crit: '0 Critical',
    meanScore: '12.4 / 100',
    primaryHazard: 'Fluoride &amp; Mineral Hardness',
    badge: 'Plateau Drainage',
    overview: 'Precambrian Vindhyan sandstone and granite base rocks. High groundwater mineralization and endemic fluoride leaching in Rohtas &amp; Sonbhadra.',
    districts: ['Sonbhadra', 'Mirzapur', 'Rohtas', 'Bhojpur', 'Arwal', 'Patna', 'Aurangabad', 'Kaimur (Bhabua)', 'Kaimur (bhabua)', 'Jehanabad', 'Nalanda', 'Gaya'],
    labelPos: { lat: 24.9, lon: 84.0, sub: '784 km · Southern Plateau' },
    cam: { x: 14, y: 28, z: 26, tx: 14, ty: 0, tz: 8 },
    centerPos: latLonToPlane(24.9, 84.0)
  }
};

const regionalRiverMeshes = {};
const riverClickObjects = [];
let regionalRiverCoreMat = null;

function buildRegionalRivers() {
  // Materials
  regionalRiverCoreMat = new THREE.MeshStandardMaterial({
    color: 0x38bdf8,
    emissive: 0x0284c7,
    emissiveIntensity: 0.85,
    roughness: 0.2,
    metalness: 0.25,
    side: THREE.DoubleSide
  });

  const riverGlowMat = new THREE.MeshBasicMaterial({
    color: 0x06b6d4,
    transparent: true,
    opacity: 0.32,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    depthWrite: false
  });

  // 1. Ganga Main Stem
  if (RIVERS.ganga_main) {
    const gangaCoreList = [];
    const gangaGlowList = [];
    RIVERS.ganga_main.forEach(line => {
      if (line.length < 2) return;
      const pts = line.map(p => {
        const { x, z } = latLonToPlane(p[1], p[0]);
        return new THREE.Vector3(x, 0.22, z);
      });
      const coreGeom = createRiverRibbonGeometry(pts, 0.62);
      const glowGeom = createRiverRibbonGeometry(pts, 1.5);
      
      const coreMesh = new THREE.Mesh(coreGeom, regionalRiverCoreMat);
      const glowMesh = new THREE.Mesh(glowGeom, riverGlowMat);
      coreMesh.position.y = 0.02;
      coreMesh.userData = { isRiver: true, riverKey: 'ganga_main' };
      glowMesh.userData = { isRiver: true, riverKey: 'ganga_main' };

      regionalRiversGroup.add(coreMesh);
      regionalRiversGroup.add(glowMesh);
      gangaCoreList.push(coreMesh);
      gangaGlowList.push(glowMesh);
      riverClickObjects.push(coreMesh);
    });
    regionalRiverMeshes['ganga_main'] = { cores: gangaCoreList, glows: gangaGlowList };
  }

  // 2. Tributaries
  if (RIVERS.tributaries) {
    const supportedTributaries = ['Yamuna', 'Gomti', 'Ghaghara', 'Gandak', 'Kosi', 'Son'];
    supportedTributaries.forEach(name => {
      const coords = RIVERS.tributaries[name];
      if (!coords || coords.length < 2) return;

      const pts = coords.map(p => {
        const { x, z } = latLonToPlane(p[1], p[0]);
        return new THREE.Vector3(x, 0.20, z);
      });
      const coreGeom = createRiverRibbonGeometry(pts, 0.44);
      const glowGeom = createRiverRibbonGeometry(pts, 1.1);

      const coreMesh = new THREE.Mesh(coreGeom, regionalRiverCoreMat);
      const glowMesh = new THREE.Mesh(glowGeom, riverGlowMat);
      coreMesh.position.y = 0.02;
      coreMesh.userData = { isRiver: true, riverKey: name };
      glowMesh.userData = { isRiver: true, riverKey: name };

      regionalRiversGroup.add(coreMesh);
      regionalRiversGroup.add(glowMesh);
      regionalRiverMeshes[name] = { cores: [coreMesh], glows: [glowMesh] };
      riverClickObjects.push(coreMesh);
    });
  }

  // 3. Floating 3D River Labels
  for (const [key, data] of Object.entries(RIVER_DATA)) {
    if (!data.labelPos) continue;
    const isMain = key === 'ganga_main';
    const labelSprite = makeRiverLabelSprite(data.name, data.labelPos.sub, isMain);
    const pos = latLonToPlane(data.labelPos.lat, data.labelPos.lon);
    labelSprite.position.set(pos.x, 2.2, pos.z);
    labelSprite.userData = { isRiverLabel: true, riverKey: key };
    regionalRiversGroup.add(labelSprite);
    if (regionalRiverMeshes[key]) {
      regionalRiverMeshes[key].labelSprite = labelSprite;
    }
  }
}
buildRegionalRivers();

// Proximity & District Mapping Helper
function getRiverForVillage(item, x, z) {
  const d = (item.district || '').trim();
  for (const [rKey, rInfo] of Object.entries(RIVER_DATA)) {
    if (rInfo.districts && rInfo.districts.includes(d)) {
      return rKey;
    }
  }
  // Spatial fallback
  let closest = 'ganga_main';
  let minD = Infinity;
  for (const [rKey, rInfo] of Object.entries(RIVER_DATA)) {
    if (!rInfo.centerPos) continue;
    const dx = x - rInfo.centerPos.x;
    const dz = z - rInfo.centerPos.z;
    const dSq = dx * dx + dz * dz;
    if (dSq < minD) {
      minD = dSq;
      closest = rKey;
    }
  }
  return closest;
}

// ═══════════════════════════════════════════════════════════
// 3D WATER SAMPLE INSTANCED NEEDLE PINS & GLOWING BEACONS (60 FPS ENGINE)
// ═══════════════════════════════════════════════════════════
const pinsGroup = new THREE.Group();
regionalGroup.add(pinsGroup);

let instancedNeedles = null;
let instancedHeads = null;
let instancedRings = null;
let instancedRingMat = null;
const cachedVillageCoords = [];

// Deterministic hash to guarantee stable, rock-solid pin coordinates across filter switches
function pseudoHash(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = (Math.imul(31, h) + str.charCodeAt(i)) | 0;
  }
  return ((h >>> 0) % 100000) / 100000;
}

const sevColors = {
  Critical: 0xef4444,
  High: 0xf97316,
  Low: 0x10b981
};

let currentActiveRiver = 'all';

function initInstancedVillagePins() {
  if (!DATA.priority || cachedVillageCoords.length > 0) return;

  DATA.priority.forEach((item, idx) => {
    const key = `${item.state}|${item.district}`;
    const centroid = DISTRICT_CENTROIDS[key] || [26.5, 82.5];
    const seed = (item.sample_id || item.ref || String(idx));
    const h1 = pseudoHash(seed + '_lat');
    const h2 = pseudoHash(seed + '_lon');
    const lat = centroid[0] + (h1 - 0.5) * 0.44;
    const lon = centroid[1] + (h2 - 0.5) * 0.44;
    const { x, z } = latLonToPlane(lat, lon);

    const itemRiver = getRiverForVillage(item, x, z);
    const score = parseFloat(item.score) || 0;
    const needleHeight = Math.max(0.65, Math.min(3.6, (score / 100) * 3.2 + 0.45));
    const colorHex = sevColors[item.band] || sevColors.Low;

    cachedVillageCoords.push({
      item,
      x,
      z,
      river: itemRiver,
      score,
      needleHeight,
      colorHex,
      band: item.band,
      visible: true,
      isCorridorMatch: true
    });
  });

  const count = cachedVillageCoords.length;
  if (count === 0) return;

  // Unit geometries (anchored at base for clean upward scaling)
  const unitCylinder = new THREE.CylinderGeometry(0.06, 0.10, 1, 6);
  unitCylinder.translate(0, 0.5, 0);

  const unitSphere = new THREE.SphereGeometry(1, 8, 8);
  const unitRing = new THREE.RingGeometry(0.25, 0.65, 16);
  unitRing.rotateX(-Math.PI / 2);

  const needleMat = new THREE.MeshStandardMaterial({
    metalness: 0.45,
    roughness: 0.35,
    transparent: true,
    opacity: 0.92
  });

  const headMat = new THREE.MeshStandardMaterial({
    metalness: 0.1,
    roughness: 0.15,
    transparent: true,
    opacity: 0.95
  });

  instancedRingMat = new THREE.MeshBasicMaterial({
    color: 0xef4444,
    transparent: true,
    opacity: 0.75,
    side: THREE.DoubleSide
  });

  instancedNeedles = new THREE.InstancedMesh(unitCylinder, needleMat, count);
  instancedHeads = new THREE.InstancedMesh(unitSphere, headMat, count);
  instancedRings = new THREE.InstancedMesh(unitRing, instancedRingMat, count);

  instancedNeedles.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  instancedHeads.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  instancedRings.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

  pinsGroup.add(instancedNeedles);
  pinsGroup.add(instancedHeads);
  pinsGroup.add(instancedRings);
}

function renderVillagePins(filterContam = 'all', activeRiver = currentActiveRiver) {
  currentActiveRiver = activeRiver;
  if (!instancedNeedles) initInstancedVillagePins();
  if (!instancedNeedles) return;

  const dummy = new THREE.Object3D();
  const tempColor = new THREE.Color();

  cachedVillageCoords.forEach((v, i) => {
    let isVisible = true;
    if (filterContam !== 'all') {
      const worst = (v.item.worst || '').toLowerCase();
      if (!worst.includes(filterContam.toLowerCase())) isVisible = false;
    }

    const isCorridorMatch = (activeRiver === 'all' || activeRiver === v.river);
    v.visible = isVisible;
    v.isCorridorMatch = isCorridorMatch;

    if (!isVisible) {
      dummy.position.set(0, -999, 0);
      dummy.scale.set(0, 0, 0);
      dummy.updateMatrix();
      instancedNeedles.setMatrixAt(i, dummy.matrix);
      instancedHeads.setMatrixAt(i, dummy.matrix);
      instancedRings.setMatrixAt(i, dummy.matrix);
      return;
    }

    // Needle Shaft
    dummy.position.set(v.x, 0, v.z);
    dummy.scale.set(1, v.needleHeight, 1);
    dummy.updateMatrix();
    instancedNeedles.setMatrixAt(i, dummy.matrix);

    // Glowing Beacon Head
    const headRadius = isCorridorMatch ? 0.17 : 0.08;
    dummy.position.set(v.x, v.needleHeight + headRadius * 0.8, v.z);
    dummy.scale.set(headRadius, headRadius, headRadius);
    dummy.updateMatrix();
    instancedHeads.setMatrixAt(i, dummy.matrix);

    // Ground Beacon Ring for Critical Stations
    if (v.band === 'Critical' && isCorridorMatch) {
      dummy.position.set(v.x, 0.04, v.z);
      dummy.scale.set(1, 1, 1);
      dummy.updateMatrix();
      instancedRings.setMatrixAt(i, dummy.matrix);
    } else {
      dummy.position.set(0, -999, 0);
      dummy.scale.set(0, 0, 0);
      dummy.updateMatrix();
      instancedRings.setMatrixAt(i, dummy.matrix);
    }

    // Color Tinting & Dynamic Luminance
    tempColor.setHex(v.colorHex);
    if (!isCorridorMatch) {
      tempColor.multiplyScalar(0.22); // Elegant dimming for stations outside focused river corridor
    }
    instancedNeedles.setColorAt(i, tempColor);

    if (v.band === 'Critical' && isCorridorMatch) {
      tempColor.setHex(0xff3333);
    }
    instancedHeads.setColorAt(i, tempColor);
  });

  instancedNeedles.instanceMatrix.needsUpdate = true;
  if (instancedNeedles.instanceColor) instancedNeedles.instanceColor.needsUpdate = true;
  instancedHeads.instanceMatrix.needsUpdate = true;
  if (instancedHeads.instanceColor) instancedHeads.instanceColor.needsUpdate = true;
  instancedRings.instanceMatrix.needsUpdate = true;
}
renderVillagePins();

/* ═══════════════════════════════════════════════════════════
   3. OPTIONAL 16K MESH GLB LOADER
   ═══════════════════════════════════════════════════════════ */
let is16kLoaded = false;
let highResMesh = null;
const btnToggleMesh = document.getElementById('btn-toggle-mesh');

btnToggleMesh.addEventListener('click', () => {
  if (is16kLoaded && highResMesh) {
    highResMesh.visible = !highResMesh.visible;
    earthMesh.visible = !highResMesh.visible;
    btnToggleMesh.textContent = highResMesh.visible ? '16K Mesh: ON' : '16K Mesh: OFF';
    btnToggleMesh.classList.toggle('active', highResMesh.visible);
    btnToggleMesh.setAttribute('aria-pressed', String(highResMesh.visible));
    return;
  }

  btnToggleMesh.textContent = 'Streaming 16K GLB…';
  const loader = new GLTFLoader();
  loader.load(
    'assets/earth_16k.glb',
    (gltf) => {
      highResMesh = gltf.scene;
      // Normalize scale to match sphere radius
      const box = new THREE.Box3().setFromObject(highResMesh);
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      const scale = (GLOBE_RADIUS * 2) / maxDim;
      highResMesh.scale.set(scale, scale, scale);
      
      globeGroup.add(highResMesh);
      earthMesh.visible = false;
      is16kLoaded = true;
      btnToggleMesh.textContent = '16K Mesh: ON';
      btnToggleMesh.classList.add('active');
      btnToggleMesh.setAttribute('aria-pressed', 'true');
    },
    (xhr) => {
      if (xhr.lengthComputable) {
        const percent = Math.round((xhr.loaded / xhr.total) * 100);
        btnToggleMesh.textContent = `16K: ${percent}%`;
      }
    },
    (err) => {
      console.warn('Could not load 16K GLB mesh:', err);
      btnToggleMesh.textContent = '16K: Failed';
      setTimeout(() => { btnToggleMesh.textContent = '16K Mesh: OFF'; }, 2000);
    }
  );
});

/* ═══════════════════════════════════════════════════════════
   4. CAMERA CHOREOGRAPHY, CUBIC FLYOVER & MODE SWITCHING
   ═══════════════════════════════════════════════════════════ */
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

// Cinema-grade cubic easing curve for silky-smooth drone deceleration
function easeInOutCubic(x) {
  return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
}

const startCamPos = camera.position.clone();
const startControlsTarget = controls.target.clone();
let targetCamPos = camera.position.clone();
let targetControlsTarget = controls.target.clone();
let isTransitioning = false;
let transitionProgress = 1;
let transitionSpeed = 1.0;
let currentModalVillageId = null;
let lastFocusedElement = null;

function flyCameraTo(targetPos, targetLookAt, duration = 1.2) {
  if (prefersReducedMotion.matches) {
    camera.position.copy(targetPos);
    controls.target.copy(targetLookAt);
    isTransitioning = false;
    transitionProgress = 1;
    return;
  }
  startCamPos.copy(camera.position);
  startControlsTarget.copy(controls.target);
  targetCamPos.copy(targetPos);
  targetControlsTarget.copy(targetLookAt);
  transitionProgress = 0;
  transitionSpeed = 1 / Math.max(0.25, duration);
  isTransitioning = true;
}

function updateURLParams() {
  let params = new URLSearchParams(window.location.search);
  params.set('mode', CURRENT_MODE);

  const activeChip = document.querySelector('.filter-chip.active');
  const activeFilter = activeChip ? activeChip.getAttribute('data-filter') : 'all';
  if (activeFilter && activeFilter !== 'all') {
    params.set('filter', activeFilter);
  } else {
    params.delete('filter');
  }

  if (currentActiveRiver && currentActiveRiver !== 'all') {
    params.set('river', currentActiveRiver);
  } else {
    params.delete('river');
  }

  const drawer = document.getElementById('simulator-drawer');
  if (drawer && drawer.classList.contains('open')) {
    params.set('sim', 'open');
  } else {
    params.delete('sim');
  }

  if (currentModalVillageId) {
    params.set('village', currentModalVillageId);
  } else {
    params.delete('village');
  }

  const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`;
  window.history.replaceState({}, '', newUrl);
}

function switchMode(mode) {
  if (mode === CURRENT_MODE && transitionProgress >= 1) return;
  CURRENT_MODE = mode;

  const btnGlobe = document.getElementById('btn-mode-globe');
  const btnReg = document.getElementById('btn-mode-regional');
  const hero = document.getElementById('hero-overlay');
  const panelLeft = document.getElementById('panel-left');
  const panelRight = document.getElementById('panel-right');

  if (mode === 'globe') {
    btnGlobe.classList.add('active');
    btnGlobe.setAttribute('aria-selected', 'true');
    btnReg.classList.remove('active');
    btnReg.setAttribute('aria-selected', 'false');

    hero.style.opacity = '1';
    hero.style.pointerEvents = 'auto';
    panelLeft.style.opacity = '0';
    panelLeft.style.pointerEvents = 'none';
    panelRight.style.opacity = '0';
    panelRight.style.pointerEvents = 'none';

    globeGroup.visible = true;
    regionalGroup.visible = false;

    flyCameraTo(
      new THREE.Vector3(indiaCenter.x * 2.3, indiaCenter.y * 1.8 + 15, indiaCenter.z * 2.3),
      new THREE.Vector3(0, 0, 0),
      1.25
    );
  } else {
    btnReg.classList.add('active');
    btnReg.setAttribute('aria-selected', 'true');
    btnGlobe.classList.remove('active');
    btnGlobe.setAttribute('aria-selected', 'false');

    hero.style.opacity = '0';
    hero.style.pointerEvents = 'none';
    panelLeft.style.opacity = '1';
    panelLeft.style.pointerEvents = 'auto';
    panelRight.style.opacity = '1';
    panelRight.style.pointerEvents = 'auto';

    globeGroup.visible = false;
    regionalGroup.visible = true;

    flyCameraTo(
      new THREE.Vector3(0, 52, 58),
      new THREE.Vector3(0, 0, 0),
      1.15
    );
  }

  updateURLParams();
}

document.getElementById('btn-mode-globe').addEventListener('click', () => switchMode('globe'));
document.getElementById('btn-mode-regional').addEventListener('click', () => switchMode('regional'));
document.getElementById('btn-hero-explore').addEventListener('click', () => switchMode('regional'));
document.getElementById('brand-home').addEventListener('click', (e) => {
  e.preventDefault();
  switchMode('globe');
});

document.getElementById('btn-camera-reset').addEventListener('click', () => {
  if (CURRENT_MODE === 'globe') {
    flyCameraTo(
      new THREE.Vector3(indiaCenter.x * 2.3, indiaCenter.y * 1.8 + 15, indiaCenter.z * 2.3),
      new THREE.Vector3(0, 0, 0),
      1.25
    );
  } else {
    flyCameraTo(
      new THREE.Vector3(0, 52, 58),
      new THREE.Vector3(0, 0, 0),
      1.15
    );
  }
});

// Raycasting for Interactivity (Water Pins & River Corridors)
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
const tooltip = document.getElementById('tooltip');
let mouseScreenX = 0;
let mouseScreenY = 0;
let isMouseOverUI = false;
let mouseNeedsRaycast = false;

window.addEventListener('mousemove', (e) => {
  mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
  mouseScreenX = e.clientX;
  mouseScreenY = e.clientY;
  isMouseOverUI = !!e.target.closest('.panel, .hud-bottom, dialog, header, .hero-overlay, .simulator-drawer');
  mouseNeedsRaycast = true;
});

window.addEventListener('click', (e) => {
  if (detailModal.open || (typeof dossierModal !== 'undefined' && dossierModal && dossierModal.open) || e.target.closest('.panel, .hud-bottom, dialog, header, .hero-overlay, .simulator-drawer')) {
    return;
  }
  if (CURRENT_MODE === 'regional' && (e.target === renderer.domElement || e.target.id === 'webgl')) {
    raycaster.setFromCamera(mouse, camera);

    // 1. Instanced water pin click -> Open Detail Modal
    if (instancedHeads) {
      const pinIntersects = raycaster.intersectObjects([instancedHeads, instancedNeedles]);
      if (pinIntersects.length > 0 && pinIntersects[0].instanceId !== undefined) {
        const v = cachedVillageCoords[pinIntersects[0].instanceId];
        if (v && v.visible) {
          openDetailModal(v.item);
          return;
        }
      }
    }

    // 2. River Ribbon click -> Focus Corridor & Telemetry
    const riverIntersects = raycaster.intersectObjects(riverClickObjects);
    if (riverIntersects.length > 0) {
      const rKey = riverIntersects[0].object.userData.riverKey;
      selectRiverCorridor(rKey, true);
      updateURLParams();
      return;
    }
  }
});


/* ═══════════════════════════════════════════════════════════
   5. PRIORITY QUEUE UI, RIVER CORRIDOR & ACCESSIBLE FILTERS
   ═══════════════════════════════════════════════════════════ */
const queueListEl = document.getElementById('queue-list');
const queueSearchEl = document.getElementById('queue-search');
const indianNumberFormat = new Intl.NumberFormat('en-IN');

function escapeHTML(str) {
  return String(str || '').replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  );
}

function formatLocationTitle(item) {
  if (!item) return 'Monitoring Source';
  if (item.village && item.village !== 'Not available' && item.village.trim() !== '') {
    return item.village;
  }
  if (item.district && item.district !== 'Not available' && item.district.trim() !== '') {
    const ref = item.ref ? ` (${item.ref})` : (item.sample_id ? ` (#${item.sample_id})` : '');
    return `${item.district} Source${ref}`;
  }
  return `Monitoring Point #${item.sample_id || '—'}`;
}

function getFilteredPriorityList() {
  if (!DATA.priority) return [];
  const activeContamChip = document.querySelector('.filter-chip.active');
  const contam = activeContamChip ? activeContamChip.getAttribute('data-filter') : 'all';
  const q = queueSearchEl.value.toLowerCase().trim();

  let list = DATA.priority;
  if (contam !== 'all') {
    list = list.filter(p => (p.worst || '').toLowerCase().includes(contam.toLowerCase()));
  }
  if (currentActiveRiver !== 'all' && RIVER_DATA[currentActiveRiver]?.districts) {
    const rDistricts = RIVER_DATA[currentActiveRiver].districts;
    list = list.filter(p => rDistricts.includes((p.district || '').trim()));
  }
  if (q) {
    list = list.filter(p =>
      (p.village || '').toLowerCase().includes(q) ||
      (p.district || '').toLowerCase().includes(q) ||
      (p.worst || '').toLowerCase().includes(q)
    );
  }
  return list;
}

function renderQueue(items) {
  queueListEl.innerHTML = '';
  document.getElementById('queue-count').textContent = `${indianNumberFormat.format(items.length)} Villages`;

  if (items.length === 0) {
    const emptyBox = document.createElement('div');
    emptyBox.className = 'empty-queue';
    emptyBox.setAttribute('role', 'status');
    const query = queueSearchEl.value.trim();
    emptyBox.innerHTML = `
      <div class="empty-queue-icon" aria-hidden="true">🔍</div>
      <strong>No Matching Water Sources Found</strong>
      <span>${query ? `No monitored sources match “${escapeHTML(query)}”.` : 'No sources currently meet the selected filter criteria.'} Try clearing search or corridor filters.</span>
      <div>
        <button type="button" class="btn-reset-search" id="btn-clear-search">Clear Search &amp; Filters</button>
      </div>
    `;
    queueListEl.appendChild(emptyBox);
    document.getElementById('btn-clear-search')?.addEventListener('click', () => {
      queueSearchEl.value = '';
      const allChip = document.querySelector('.filter-chip[data-filter="all"]');
      if (allChip) {
        document.querySelectorAll('.filter-chip').forEach(c => {
          c.classList.remove('active');
          c.setAttribute('aria-pressed', 'false');
        });
        allChip.classList.add('active');
        allChip.setAttribute('aria-pressed', 'true');
      }
      selectRiverCorridor('all', false);
      renderVillagePins('all', 'all');
      renderQueue(DATA.priority || []);
      updateURLParams();
    });
    return;
  }

  // Pretext font spec: 600 13px Inter
  const cardFontSpec = '600 13px Inter, -apple-system, sans-serif';

  items.slice(0, 100).forEach(item => {
    const locTitle = formatLocationTitle(item);
    // Pretext DOM-free measurement: precompute line breaks and height without triggering browser reflow
    let isMultiLine = false;
    try {
      const prepared = prepare(locTitle, cardFontSpec);
      const measured = layout(prepared, 185, 16);
      isMultiLine = measured.lineCount > 1;
    } catch {
      // Fallback if offscreen canvas measurement fails
    }

    const card = document.createElement('button');
    card.type = 'button';
    card.className = `queue-card${isMultiLine ? ' multi-line' : ''}`;
    card.setAttribute('aria-label', `View laboratory telemetry report for ${locTitle}, severity ${item.band}, risk score ${item.score}`);

    const scoreColor = item.band === 'Critical' ? '#ef4444' : item.band === 'High' ? '#f97316' : '#10b981';
    card.innerHTML = `
      <div class="q-row-top">
        <span class="q-village" title="${escapeHTML(locTitle)}">${escapeHTML(locTitle)}</span>
        <span class="q-score" style="color:${scoreColor}">
          ${item.score}
        </span>
      </div>
      <div class="q-meta">${escapeHTML(item.district)} · ${escapeHTML(item.state)}</div>
      <div class="q-tags">
        <span class="q-badge ${item.band}">${item.band}</span>
        <span class="q-contam">${escapeHTML(item.worst || 'Normal')}</span>
      </div>
    `;

    card.addEventListener('click', () => {
      lastFocusedElement = card;
      openDetailModal(item);
    });

    queueListEl.appendChild(card);
  });
}

if (DATA.priority) renderQueue(DATA.priority);

// Search Filtering
queueSearchEl.addEventListener('input', () => {
  renderQueue(getFilteredPriorityList());
});

// Contaminant Filter Buttons
const filterChips = document.querySelectorAll('.filter-chip');
filterChips.forEach(chip => {
  chip.addEventListener('click', () => {
    filterChips.forEach(c => {
      c.classList.remove('active');
      c.setAttribute('aria-pressed', 'false');
    });
    chip.classList.add('active');
    chip.setAttribute('aria-pressed', 'true');
    const filter = chip.getAttribute('data-filter') || 'all';
    renderVillagePins(filter, currentActiveRiver);
    renderQueue(getFilteredPriorityList());
    updateURLParams();
  });
});

// River Corridor Selection & Telemetry Function
function selectRiverCorridor(riverKey, animateCamera = true) {
  if (!RIVER_DATA[riverKey]) riverKey = 'all';
  currentActiveRiver = riverKey;

  // 1. Update UI chips
  const rChips = document.querySelectorAll('.river-chip');
  rChips.forEach(c => {
    const match = c.getAttribute('data-river') === riverKey;
    c.classList.toggle('active', match);
    c.setAttribute('aria-pressed', String(match));
  });

  // 2. Update telemetry card
  const rInfo = RIVER_DATA[riverKey];
  const elName = document.getElementById('rex-river-name');
  const elLen = document.getElementById('rex-river-length');
  const elStn = document.getElementById('rex-stat-stations');
  const elCrit = document.getElementById('rex-stat-crit');
  const elScore = document.getElementById('rex-stat-score');
  const elHz = document.getElementById('rex-stat-hazard');
  const elThreat = document.getElementById('rex-threat-box');
  const elBadge = document.getElementById('rex-corridor-badge');

  if (elName) elName.textContent = rInfo.name;
  if (elLen) elLen.textContent = rInfo.length;
  if (elStn) elStn.textContent = rInfo.stations;
  if (elCrit) elCrit.textContent = rInfo.crit;
  if (elScore) elScore.textContent = rInfo.meanScore;
  if (elHz) elHz.textContent = rInfo.primaryHazard;
  if (elThreat) {
    elThreat.innerHTML = `<strong>${riverKey === 'all' ? 'Basin Overview:' : 'Corridor Hydrology:'}</strong> ${rInfo.overview}`;
  }
  if (elBadge) elBadge.textContent = rInfo.badge;

  // 3. Re-render pins with highlighting & opacity falloff
  const activeContamChip = document.querySelector('.filter-chip.active');
  const activeContam = activeContamChip ? activeContamChip.getAttribute('data-filter') : 'all';
  renderVillagePins(activeContam, riverKey);

  // 4. Update River Ribbon Luminance
  for (const [key, meshObj] of Object.entries(regionalRiverMeshes)) {
    const isSelected = (riverKey === 'all' || key === riverKey);
    const intensity = (key === riverKey) ? 1.5 : (riverKey === 'all' ? 0.85 : 0.22);
    if (meshObj.cores) {
      meshObj.cores.forEach(mesh => {
        if (mesh.material) {
          mesh.material.emissiveIntensity = intensity;
          mesh.material.opacity = isSelected ? 1.0 : 0.2;
        }
      });
    }
    if (meshObj.glows) {
      meshObj.glows.forEach(mesh => {
        if (mesh.material) {
          mesh.material.opacity = (key === riverKey) ? 0.65 : (riverKey === 'all' ? 0.32 : 0.08);
        }
      });
    }
    if (meshObj.labelSprite) {
      meshObj.labelSprite.visible = (riverKey === 'all' || key === riverKey);
    }
  }

  // 5. Animate Camera smoothly if requested
  if (animateCamera && rInfo.cam) {
    flyCameraTo(
      new THREE.Vector3(rInfo.cam.x, rInfo.cam.y, rInfo.cam.z),
      new THREE.Vector3(rInfo.cam.tx, rInfo.cam.ty, rInfo.cam.tz),
      1.15
    );
  }

  // 6. Filter Priority Queue
  renderQueue(getFilteredPriorityList());
}

// River Corridor UI Listeners
const rChips = document.querySelectorAll('.river-chip');
rChips.forEach(chip => {
  chip.addEventListener('click', () => {
    const rKey = chip.getAttribute('data-river') || 'all';
    selectRiverCorridor(rKey, true);
    updateURLParams();
  });
});

document.getElementById('btn-rex-focus')?.addEventListener('click', () => {
  selectRiverCorridor(currentActiveRiver, true);
});

document.getElementById('btn-rex-reset')?.addEventListener('click', () => {
  selectRiverCorridor('all', true);
  updateURLParams();
});

/* ═══════════════════════════════════════════════════════════
   6. WHAT-IF PARAMETER SIMULATOR
   ═══════════════════════════════════════════════════════════ */
const drawer = document.getElementById('simulator-drawer');
const btnToggleSim = document.getElementById('btn-toggle-sim');
const btnCloseSim = document.getElementById('btn-close-sim');

btnToggleSim.addEventListener('click', () => {
  const isOpen = drawer.classList.toggle('open');
  btnToggleSim.setAttribute('aria-expanded', String(isOpen));
  if (isOpen) {
    lastFocusedElement = btnToggleSim;
    btnCloseSim.focus();
  }
  updateURLParams();
});

btnCloseSim.addEventListener('click', () => {
  drawer.classList.remove('open');
  btnToggleSim.setAttribute('aria-expanded', 'false');
  btnToggleSim.focus();
  updateURLParams();
});

const simInputs = {
  arsenic: document.getElementById('range-arsenic'),
  fluoride: document.getElementById('range-fluoride'),
  ecoli: document.getElementById('range-ecoli'),
  nitrate: document.getElementById('range-nitrate'),
  iron: document.getElementById('range-iron')
};

function calculateSimulation() {
  const as = parseFloat(simInputs.arsenic.value);
  const f = parseFloat(simInputs.fluoride.value);
  const ec = parseFloat(simInputs.ecoli.value);
  const no3 = parseFloat(simInputs.nitrate.value);
  const fe = parseFloat(simInputs.iron.value);

  document.getElementById('val-arsenic').innerHTML = `${as.toFixed(3)}&nbsp;mg/L`;
  document.getElementById('val-fluoride').innerHTML = `${f.toFixed(1)}&nbsp;mg/L`;
  document.getElementById('val-ecoli').innerHTML = `${Math.round(ec)}&nbsp;MPN`;
  document.getElementById('val-nitrate').innerHTML = `${Math.round(no3)}&nbsp;mg/L`;
  document.getElementById('val-iron').innerHTML = `${fe.toFixed(1)}&nbsp;mg/L`;

  // BIS 10500 Severity calculation
  // Arsenic: acc 0.01, perm 0.05, weight 1.0
  const sevAs = as <= 0.01 ? 0 : as >= 0.05 ? 1.0 : (as - 0.01) / 0.04;
  // Fluoride: acc 1.0, perm 1.5, weight 0.8
  const sevF = f <= 1.0 ? 0 : f >= 1.5 ? 1.0 : (f - 1.0) / 0.5;
  // E. coli: acc 0, weight 0.9
  const sevEc = ec > 0 ? 1.0 : 0;
  // Nitrate: acc 45, perm 45, weight 0.7
  const sevNo3 = no3 <= 45 ? 0 : 1.0;
  // Iron: acc 1.0, weight 0.4
  const sevFe = fe <= 1.0 ? 0 : 1.0;

  const weights = 1.0 + 0.8 + 0.9 + 0.7 + 0.4;
  const weightedSum = (sevAs * 1.0) + (sevF * 0.8) + (sevEc * 0.9) + (sevNo3 * 0.7) + (sevFe * 0.4);
  let score = Math.round((weightedSum / weights) * 100);

  // Acute hazard escalation
  if (sevEc > 0 || as >= 0.05) {
    score = Math.max(score, 75);
  } else if (sevF >= 1.0 || sevNo3 >= 1.0) {
    score = Math.max(score, 50);
  }

  const scoreEl = document.getElementById('sim-score-num');
  const badgeEl = document.getElementById('sim-badge');
  const recEl = document.getElementById('sim-rec-text');

  scoreEl.textContent = score.toFixed(1);

  let recText = '';
  if (score >= 75) {
    scoreEl.style.color = '#ef4444';
    badgeEl.textContent = 'CRITICAL RISK';
    badgeEl.style.background = 'rgba(239, 68, 68, 0.2)';
    badgeEl.style.color = '#ef4444';
    badgeEl.style.border = '1px solid rgba(239, 68, 68, 0.4)';
    recText = sevEc > 0 
      ? 'IMMEDIATE HAZARD: Bacterial contamination detected. Issue boil-water advisory and initiate sodium hypochlorite shock-chlorination.'
      : 'ACUTE TOXICITY: Arsenic levels exceed permissible threshold. Deploy Adsorptive Coagulation / Arsenic-Removal Unit & switch to deep aquifers.';
  } else if (score >= 50) {
    scoreEl.style.color = '#f97316';
    badgeEl.textContent = 'HIGH RISK';
    badgeEl.style.background = 'rgba(249, 115, 22, 0.2)';
    badgeEl.style.color = '#f97316';
    badgeEl.style.border = '1px solid rgba(249, 115, 22, 0.4)';
    recText = sevF >= 1.0 
      ? 'Fluoride exceedance detected. High risk of dental/skeletal fluorosis. Deploy Nalgonda defluoridation plant or activated alumina filter.'
      : 'Elevated chemical contaminants. Prioritize community filtration and source blending.';
  } else {
    scoreEl.style.color = '#10b981';
    badgeEl.textContent = 'SAFE (LOW)';
    badgeEl.style.background = 'rgba(16, 185, 129, 0.15)';
    badgeEl.style.color = '#10b981';
    badgeEl.style.border = '1px solid rgba(16, 185, 129, 0.3)';
    recText = 'All simulated parameters are within safe BIS IS 10500 standards. Regular seasonal surveillance recommended.';
  }
  recEl.textContent = recText;

  // Pretext: compute exact dynamic height for recommendation box to eliminate layout shift
  try {
    const recPrepared = prepare(recText, '400 12px Inter, -apple-system, sans-serif');
    const recMeasured = layout(recPrepared, 280, 18);
    recEl.style.minHeight = `${Math.max(recMeasured.height, 36)}px`;
  } catch {}
}

Object.values(simInputs).forEach(inp => inp.addEventListener('input', calculateSimulation));
calculateSimulation();

/* ═══════════════════════════════════════════════════════════
   7. VILLAGE DETAIL MODAL
   ═══════════════════════════════════════════════════════════ */
const detailModal = document.getElementById('detail-modal');
const btnCloseModal = document.getElementById('btn-close-modal');

btnCloseModal.addEventListener('click', (e) => {
  e.stopPropagation();
  detailModal.close();
  currentModalVillageId = null;
  updateURLParams();
  if (lastFocusedElement) {
    lastFocusedElement.focus();
  }
});

detailModal.addEventListener('close', () => {
  currentModalVillageId = null;
  updateURLParams();
  if (lastFocusedElement) {
    lastFocusedElement.focus();
  }
});

function openDetailModal(item) {
  currentModalVillageId = item.sample_id || item.ref;
  updateURLParams();

  const locTitle = formatLocationTitle(item);
  document.getElementById('modal-village-name').textContent = locTitle;
  document.getElementById('modal-village-meta').textContent = `${item.district}, ${item.state} · Sample ID: ${item.ref || item.sample_id}`;

  const readingsBody = document.getElementById('modal-readings-body');
  readingsBody.innerHTML = '';

  const details = DATA.details && DATA.details[String(item.sample_id)];
  if (details && details.readings && details.readings.length > 0) {
    details.readings.forEach(r => {
      const isExceeded = r.permissible ? (r.value > r.permissible) : (r.acceptable ? r.value > r.acceptable : false);
      const isSafe = r.acceptable ? r.value <= r.acceptable : true;
      const statusText = isExceeded ? 'EXCEEDED' : (isSafe ? 'SAFE' : 'ACCEPTABLE');
      const statusColor = isExceeded ? '#ef4444' : (isSafe ? '#10b981' : '#f97316');

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="font-weight:600;">${escapeHTML(r.parameter_key)}</td>
        <td style="font-family:var(--mono); font-variant-numeric:tabular-nums; color:#fff;">${r.value}&nbsp;<small style="color:var(--text-dim);">${escapeHTML(r.unit || '')}</small></td>
        <td style="font-family:var(--mono); font-variant-numeric:tabular-nums; color:var(--text-muted);">${r.acceptable ?? '—'}</td>
        <td style="font-family:var(--mono); font-variant-numeric:tabular-nums; color:var(--text-muted);">${r.permissible ?? 'No relaxation'}</td>
        <td style="font-family:var(--mono); font-weight:700; color:${statusColor}">${statusText}</td>
      `;
      readingsBody.appendChild(tr);
    });
  } else {
    readingsBody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-dim); padding:16px;">Telemetry records mapped to district aggregation (${escapeHTML(item.worst || 'Normal')}).</td></tr>`;
  }

  // Recurrence Info
  const recEl = document.getElementById('modal-recurrence-info');
  if (details && details.hist_count > 0) {
    recEl.innerHTML = `
      <span style="color:#f87171; font-weight:600;">Chronic Recurrence Flagged:</span> Detected in ${details.hist_count} previous testing cycles across years [${details.hist_years.join(', ')}]. Contaminants: <strong>${escapeHTML(details.hist_params.join(', '))}</strong>.
    `;
  } else {
    recEl.textContent = 'No previous recurring contamination recorded in the 2009–2012 baseline registry.';
  }

  // Action Recommendation
  const actionEl = document.getElementById('modal-intervention-info');
  const worst = (item.worst || '').toLowerCase();
  if (worst.includes('arsenic')) {
    actionEl.innerHTML = '<strong>Action Required:</strong> Immediate installation of community-scale Adsorptive Media Arsenic Removal Plant (AMARP) and exploratory deep aquifer tube-well drilling beyond 120m.';
  } else if (worst.includes('fluoride')) {
    actionEl.innerHTML = '<strong>Action Required:</strong> Deployment of CSIR-NEERI Nalgonda defluoridation filter or Activated Alumina unit. Distribute safe drinking water tankers in affected school habitations.';
  } else if (worst.includes('coli')) {
    actionEl.innerHTML = '<strong>Action Required:</strong> Immediate sanitary survey for pit-latrine seepage. Perform shock chlorination at source and install automated inline chemical chlorinator.';
  } else if (worst.includes('iron')) {
    actionEl.innerHTML = '<strong>Action Required:</strong> Install aeration-cum-sand-gravel Iron Removal Plant (IRP) at source hand-pump.';
  } else {
    actionEl.innerHTML = '<strong>Surveillance Mode:</strong> Parameters comply with Bureau of Indian Standards (BIS IS 10500). Maintain scheduled post-monsoon testing protocol.';
  }

  detailModal.showModal();
  btnCloseModal.focus();
}

/* ═══════════════════════════════════════════════════════════
   8. ACADEMIC DOSSIER, TELEMETRY EXPORT & KEYBOARD COMMAND DECK
   ═══════════════════════════════════════════════════════════ */
const dossierModal = document.getElementById('dossier-modal');
const btnProjectInfo = document.getElementById('btn-project-info');
const btnCloseDossier = document.getElementById('btn-close-dossier');

btnProjectInfo?.addEventListener('click', () => {
  lastFocusedElement = btnProjectInfo;
  dossierModal.showModal();
  btnCloseDossier.focus();
});

btnCloseDossier?.addEventListener('click', () => {
  dossierModal.close();
  if (lastFocusedElement) lastFocusedElement.focus();
});

// Station Telemetry JSON Export (Dossier Generator for Evaluators)
document.getElementById('btn-export-station')?.addEventListener('click', () => {
  if (!currentModalVillageId || !DATA.priority) return;
  const village = DATA.priority.find(p => String(p.sample_id) === String(currentModalVillageId) || String(p.ref) === String(currentModalVillageId));
  if (!village) return;
  const details = DATA.details && DATA.details[String(village.sample_id)];
  const exportPayload = {
    metadata: {
      project: 'WaterTriage: AI-Driven Drinking Water Quality Triage & Spatiotemporal Contamination Mapping',
      regulatory_standard: 'Bureau of Indian Standards BIS IS 10500:2012 Drinking Water Specification (Second Revision)',
      academic_supervision: {
        guide: 'Dr. Girish Paliwal',
        author: 'Anubhav Anand (Enrollment: A41105223039)',
        department: 'Department of Computer Science & Engineering, Amity School of Engineering & Technology',
        institution: 'Amity University Uttar Pradesh'
      },
      export_timestamp: new Date().toISOString()
    },
    monitoring_station: {
      sample_id: village.sample_id,
      ref_id: village.ref,
      location_title: formatLocationTitle(village),
      district: village.district,
      state: village.state,
      risk_score: village.score,
      severity_band: village.band,
      primary_contaminant: village.worst || 'Normal'
    },
    bis_is_10500_telemetry: details?.readings || [],
    historical_surveillance_baseline: {
      recurring_incidents_recorded: details?.hist_count || 0,
      survey_years: details?.hist_years || [],
      recurrent_parameters: details?.hist_params || []
    }
  };
  const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `watertriage_station_${village.district}_${village.sample_id || village.ref}.json`;
  a.click();
  URL.revokeObjectURL(url);
});

// Live Framerate Telemetry Meter
let frameCount = 0;
let lastFpsTime = performance.now();
const elFps = document.getElementById('fps-val');

function updateFpsMeter() {
  frameCount++;
  const now = performance.now();
  if (now - lastFpsTime >= 500) {
    const fps = Math.round((frameCount * 1000) / (now - lastFpsTime));
    if (elFps) elFps.textContent = String(Math.min(fps, 60));
    frameCount = 0;
    lastFpsTime = now;
  }
}

/* ═══════════════════════════════════════════════════════════
   9. ANIMATION & 60 FPS RENDER LOOP
   ═══════════════════════════════════════════════════════════ */
const clock = new THREE.Clock();

function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  updateFpsMeter();

  // Smooth Cubic Camera Interpolation
  if (isTransitioning) {
    transitionProgress += delta * transitionSpeed;
    if (transitionProgress >= 1) {
      transitionProgress = 1;
      isTransitioning = false;
      camera.position.copy(targetCamPos);
      controls.target.copy(targetControlsTarget);
    } else {
      const t = easeInOutCubic(transitionProgress);
      camera.position.lerpVectors(startCamPos, targetCamPos, t);
      controls.target.lerpVectors(startControlsTarget, targetControlsTarget, t);
    }
  }

  // Subtle Globe rotation in Globe Mode (idle) only if user has not requested reduced motion
  if (CURRENT_MODE === 'globe' && controls.state === -1 && !prefersReducedMotion.matches) {
    globeGroup.rotation.y += 0.0006;
  }

  // Luminous water flow shimmer for river ribbons in Regional Mode
  if (CURRENT_MODE === 'regional' && regionalRiverCoreMat && !prefersReducedMotion.matches) {
    const t = clock.getElapsedTime();
    regionalRiverCoreMat.emissiveIntensity = 0.78 + Math.sin(t * 2.5) * 0.18;
    if (instancedRingMat) {
      instancedRingMat.opacity = 0.55 + Math.sin(t * 3.5) * 0.25;
    }
  }

  // High-performance throttled raycasting (runs once per animation frame)
  if (CURRENT_MODE === 'regional' && mouseNeedsRaycast && !isMouseOverUI && instancedHeads) {
    mouseNeedsRaycast = false;
    raycaster.setFromCamera(mouse, camera);

    let hasHover = false;
    const pinIntersects = raycaster.intersectObjects([instancedHeads, instancedNeedles]);
    if (pinIntersects.length > 0 && pinIntersects[0].instanceId !== undefined) {
      const v = cachedVillageCoords[pinIntersects[0].instanceId];
      if (v && v.visible) {
        tooltip.style.display = 'flex';
        tooltip.style.left = `${mouseScreenX}px`;
        tooltip.style.top = `${mouseScreenY}px`;
        tooltip.setAttribute('aria-hidden', 'false');
        document.getElementById('tt-title').textContent = formatLocationTitle(v.item);
        const rName = v.river && RIVER_DATA[v.river] ? ` · ${RIVER_DATA[v.river].name}` : '';
        document.getElementById('tt-sub').textContent = `${v.item.district}, ${v.item.state}${rName}`;
        const ttScore = document.getElementById('tt-score');
        ttScore.textContent = `Score: ${v.item.score} (${v.item.band})`;
        ttScore.style.color = v.item.band === 'Critical' ? '#ef4444' : v.item.band === 'High' ? '#f97316' : '#10b981';
        document.body.style.cursor = 'pointer';
        hasHover = true;
      }
    }

    if (!hasHover) {
      const riverIntersects = raycaster.intersectObjects(riverClickObjects);
      if (riverIntersects.length > 0) {
        const rKey = riverIntersects[0].object.userData.riverKey;
        const rData = RIVER_DATA[rKey];
        if (rData) {
          tooltip.style.display = 'flex';
          tooltip.style.left = `${mouseScreenX}px`;
          tooltip.style.top = `${mouseScreenY}px`;
          tooltip.setAttribute('aria-hidden', 'false');
          document.getElementById('tt-title').textContent = `🌊 ${rData.name}`;
          document.getElementById('tt-sub').textContent = `${rData.length} · ${rData.stations}`;
          const ttScore = document.getElementById('tt-score');
          ttScore.textContent = `Hazard: ${rData.primaryHazard}`;
          ttScore.style.color = '#38bdf8';
          document.body.style.cursor = 'pointer';
          hasHover = true;
        }
      }
    }

    if (!hasHover) {
      tooltip.style.display = 'none';
      tooltip.setAttribute('aria-hidden', 'true');
      document.body.style.cursor = 'default';
    }
  } else if (isMouseOverUI) {
    tooltip.style.display = 'none';
    tooltip.setAttribute('aria-hidden', 'true');
    document.body.style.cursor = 'default';
  }

  controls.update();
  renderer.render(scene, camera);
}

// Pre-compile all WebGL shaders ahead of time to eliminate any initial frame drops
try {
  renderer.compile(scene, camera);
} catch (e) {}

animate();

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// Full Keyboard Command Deck for Power Users
window.addEventListener('keydown', (e) => {
  const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
  const isInputActive = (activeTag === 'input' || activeTag === 'textarea' || document.activeElement.isContentEditable);

  if (e.key === 'Escape') {
    if (dossierModal && dossierModal.open) {
      dossierModal.close();
      if (lastFocusedElement) lastFocusedElement.focus();
    } else if (detailModal.open) {
      detailModal.close();
      currentModalVillageId = null;
      updateURLParams();
      if (lastFocusedElement) lastFocusedElement.focus();
    } else if (drawer.classList.contains('open')) {
      drawer.classList.remove('open');
      btnToggleSim.setAttribute('aria-expanded', 'false');
      btnToggleSim.focus();
      updateURLParams();
    }
    return;
  }

  // Avoid hotkeys when typing in search input
  if (isInputActive) return;

  if (e.key === '1') {
    e.preventDefault();
    switchMode('globe');
  } else if (e.key === '2') {
    e.preventDefault();
    switchMode('regional');
  } else if (e.key === 's' || e.key === 'S') {
    e.preventDefault();
    btnToggleSim.click();
  } else if (e.key === 'i' || e.key === 'I') {
    e.preventDefault();
    if (dossierModal.open) {
      dossierModal.close();
      if (lastFocusedElement) lastFocusedElement.focus();
    } else {
      lastFocusedElement = document.activeElement;
      dossierModal.showModal();
      btnCloseDossier.focus();
    }
  } else if (e.key === '/') {
    e.preventDefault();
    if (CURRENT_MODE !== 'regional') {
      switchMode('regional');
    }
    queueSearchEl.focus();
    queueSearchEl.select();
  }
});

/* ═══════════════════════════════════════════════════════════
   10. INITIAL URL STATE RESTORATION
   ═══════════════════════════════════════════════════════════ */
function restoreStateFromURL() {
  let params = new URLSearchParams(window.location.search);
  const modeParam = params.get('mode');
  const filterParam = params.get('filter');
  const riverParam = params.get('river');
  const simParam = params.get('sim');
  const villageParam = params.get('village');

  if (modeParam === 'regional') {
    switchMode('regional');
  }
  if (filterParam) {
    const matchingChip = document.querySelector(`.filter-chip[data-filter="${filterParam}"]`);
    if (matchingChip) matchingChip.click();
  }
  if (riverParam && RIVER_DATA[riverParam]) {
    selectRiverCorridor(riverParam, false);
  }
  if (simParam === 'open') {
    drawer.classList.add('open');
    btnToggleSim.setAttribute('aria-expanded', 'true');
  }
  if (villageParam && DATA.priority) {
    const village = DATA.priority.find(p => String(p.sample_id) === String(villageParam) || String(p.ref) === String(villageParam));
    if (village) openDetailModal(village);
  }
}

// Restore state once data is populated
setTimeout(restoreStateFromURL, 150);
}
