const SnakeGameShared = window.SnakeGameShared;
if (!SnakeGameShared) {
  throw new Error("Snake shared helpers failed to load.");
}

const {
  C,
  DIR_BY_KEY,
  DOWN,
  LEFT,
  RIGHT,
  UP,
  angleLerpShortest,
  copySubImage,
  createCanvas,
  drawCapsule,
  easeOutQuad,
  lerp,
  lerpPt,
  loadAssets,
  mixColor,
  rgba,
  rotatePoint,
  scaleCanvas,
  scaleCanvasFitWidth,
  smoothstep,
  triangleSample,
  vecLen,
} = SnakeGameShared;


class SnakeWeb {
  constructor() {
    this.page = document.querySelector(".page");
    this.frame = document.getElementById("game-frame");
    this.canvas = document.getElementById("game-canvas");
    this.ctx = this.canvas.getContext("2d");
    this.raw = {};
    this.assets = {};
    this.audio = {};
    this.loaded = false;
    this.running = true;
    this.maximized = false;
    this.pointer = { x: -1, y: -1 };
    this.xRect = null;
    this.fsRect = null;
    this.volRect = null;
    this.playButtonRect = null;
    this.clearStoredHighScore();
    this.highScore = 0;
    this.trophyUnlockedAfterRestart = false;
    this.audioMuted = false;
    this.audioUnlocked = false;
    this.lastFrameTime = performance.now();
    this.resetOverlayState();
    this.newGame();
    this.showStarterCard("launch", 0);
    this.bindEvents();
    this.resizeCanvasBuffer();
    this.drawBootFrame();
    this.loadAssets()
      .then(() => {
        this.loaded = true;
        this.scheduleNextTongueRattle(this.now());
        this.scheduleNextEyeBlink(this.now());
        this.draw();
        requestAnimationFrame((ts) => this.loop(ts));
      })
      .catch((error) => {
        console.error("Snake web boot failed", error);
        this.drawBootFrame();
      });
  }

  now() {
    return performance.now();
  }

  clearStoredHighScore() {
    try {
      window.sessionStorage.removeItem("snake-high-score");
    } catch {
      // Ignore file:// storage failures.
    }
    try {
      window.localStorage.removeItem("snake-high-score");
    } catch {
      // Ignore file:// storage failures.
    }
  }

  saveHighScore() {
    // Browser high score is in-memory only.
  }

  bindEvents() {
    window.addEventListener("resize", () => this.resizeCanvasBuffer());
    window.addEventListener("keydown", (event) => this.handleKeyDown(event));
    this.canvas.addEventListener("mousemove", (event) => this.handlePointerMove(event));
    this.canvas.addEventListener("mouseleave", () => {
      this.pointer = { x: -1, y: -1 };
      this.updateCursor();
    });
    this.canvas.addEventListener("mousedown", (event) => this.handleMouseDown(event));
  }

  updateFrameSize() {
    const viewportW = Math.max(1, window.innerWidth || document.documentElement.clientWidth || C.BASE_W);
    const viewportH = Math.max(1, window.innerHeight || document.documentElement.clientHeight || C.BASE_H);
    const totalPadX = this.maximized ? C.BROWSER_MAXIMIZED_TOTAL_PAD_X : C.BROWSER_DEFAULT_TOTAL_PAD_X;
    const totalPadY = this.maximized ? C.BROWSER_MAXIMIZED_TOTAL_PAD_Y : C.BROWSER_DEFAULT_TOTAL_PAD_Y;
    const sizeCap = this.maximized ? Number.POSITIVE_INFINITY : C.BROWSER_DEFAULT_MAX_SIZE;
    const size = Math.max(
      280,
      Math.floor(Math.min(viewportW - totalPadX, viewportH - totalPadY, sizeCap)),
    );
    this.frame.style.width = `${size}px`;
    this.frame.style.height = `${size}px`;
  }

  resizeCanvasBuffer() {
    this.updateFrameSize();
    const dpr = Math.max(1, window.devicePixelRatio || 1);
    const rect = this.frame.getBoundingClientRect();
    this.canvas.width = Math.max(1, Math.round(rect.width * dpr));
    this.canvas.height = Math.max(1, Math.round(rect.height * dpr));
    this.ctx.setTransform(this.canvas.width / C.BASE_W, 0, 0, this.canvas.height / C.BASE_H, 0, 0);
    this.ctx.imageSmoothingEnabled = true;
    if (this.loaded) {
      this.draw();
    } else {
      this.drawBootFrame();
    }
  }

  async loadAssets() {
    await loadAssets(this);
  }

  resetOverlayState({ keepWaitingCue = false } = {}) {
    this.playButtonRect = null;
    this.starterCardVisible = false;
    this.starterCardContext = null;
    this.starterCardRevealMs = null;
    this.starterCardRunScore = 0;
    this.showWaitingStartCue = keepWaitingCue;
  }

  showStarterCard(context, runScore = 0, revealMs = null) {
    this.starterCardContext = context;
    this.starterCardRunScore = Math.max(0, Math.trunc(runScore));
    this.starterCardRevealMs = revealMs;
    this.starterCardVisible = revealMs === null;
    this.showWaitingStartCue = false;
    this.playButtonRect = null;
  }

  hideStarterCard() {
    this.resetOverlayState({ keepWaitingCue: this.showWaitingStartCue });
  }

  showWaitingCue() {
    this.showWaitingStartCue = true;
    this.hideStarterCard();
  }

  refreshStarterCardVisibility(nowMs) {
    if (this.starterCardVisible || this.starterCardRevealMs === null) {
      return;
    }
    if (nowMs < this.starterCardRevealMs) {
      return;
    }
    this.starterCardVisible = true;
    this.starterCardRevealMs = null;
  }

  newGame() {
    this.stopAudio();
    this.score = 0;
    this.gameState = "waiting";
    this.tailDarkness = 0;
    this.pendingGrowth = 0;
    this.resetOverlayState();
    const { snake, apple } = this.buildStartingPositions();
    this.snake = snake;
    this.apple = apple;
    const nowMs = this.now();
    this.resetMovementState(nowMs);
    this.resetAnimationState(nowMs);
  }

  buildStartingPositions() {
    const cx = Math.floor(C.GRID_COLS / 2);
    const cy = Math.floor(C.GRID_ROWS / 2);
    const headX = cx - (C.START_SNAKE_SEGMENTS + 1);
    const snake = [];
    for (let offset = 0; offset < C.START_SNAKE_SEGMENTS; offset += 1) {
      snake.push([headX - offset, cy]);
    }
    return { snake, apple: [cx + 3, cy] };
  }

  resetMovementState(nowMs) {
    this.direction = RIGHT.slice();
    this.nextDir = RIGHT.slice();
    this.inputQueue = [];
    this.inputQueueMax = 4;
    this.startMoveLocked = false;
    this.prevHead = this.snake[0].slice();
    this.prevTail = this.snake[this.snake.length - 1].slice();
    this.prevDirection = this.direction.slice();
    this.lastFrameMs = nowMs;
    this.headAngleDeg = this.dirToAngle(this.direction);
    this.turnFromDeg = this.headAngleDeg;
    this.turnToDeg = this.headAngleDeg;
    this.turnStartMs = nowMs;
    this.turnEndMs = nowMs;
    this.headFloat = this.snake[0].map((value) => Number(value));
    this.moveSpeed = 1000 / C.TICK_RATE;
    this.bodyPath = [];
    this.rebuildBodyPath();
    this.lastHeadCell = this.snake[0].slice();
    this.lastTurnCell = null;
  }

  resetAnimationState(nowMs) {
    this.applePulseFrozen = 1.0;
    this.mouthPhase = 0.0;
    this.mouthTargetOpen = false;
    this.mouthLastUpdateMs = nowMs;
    this.mouthFrameIdx = 0;
    this.mouthCloseDelayUntilMs = 0;
    this.tongueAnimActive = false;
    this.tongueAnimPhase = 0.0;
    this.tongueAnimDir = 1;
    this.tongueLastUpdateMs = nowMs;
    this.tongueFrameIdx = 0;
    this.tongueNextRattleMs = nowMs;
    this.scheduleNextTongueRattle(nowMs);
    this.eyeBlinkActive = false;
    this.eyeFrameIdx = 0;
    this.eyeLastUpdateMs = nowMs;
    this.eyeNextBlinkMs = nowMs;
    this.scheduleNextEyeBlink(nowMs);
    this.bulges = [];
    this.growthHiddenTiles = 0;
    this.collisionShakeStartMs = 0;
    this.collisionShakeEndMs = 0;
    this.resetRecoilPathHistory();
    this.collisionRecoil = null;
    this.deathPose = null;
    this.deathFaceAnim = null;
    this.collisionEffect = null;
    this.deathOverlayDelayUntilMs = 0;
  }

  dirToAngle(dir) {
    if (dir[0] === 1 && dir[1] === 0) {
      return 0;
    }
    if (dir[0] === 0 && dir[1] === 1) {
      return 90;
    }
    if (dir[0] === -1 && dir[1] === 0) {
      return 180;
    }
    return -90;
  }

  angleVec(angleDeg) {
    const rad = angleDeg * Math.PI / 180;
    return [Math.cos(rad), Math.sin(rad)];
  }

  layout() {
    const headerH = C.HEADER_H;
    const tileSize = C.TILE_SIZE;
    const boardW = tileSize * C.GRID_COLS;
    const boardH = tileSize * C.GRID_ROWS;
    const boardOx = Math.floor((C.BASE_W - boardW) / 2);
    const boardOy = headerH + Math.floor((C.BASE_H - headerH - boardH) / 2);
    return {
      sc: 1,
      headerH,
      tileSize,
      boardW,
      boardH,
      boardOx,
      boardOy,
      winW: C.BASE_W,
      winH: C.BASE_H,
      bodyR: Math.max(1, Math.floor((tileSize - 8) / 2)),
    };
  }

  gridToPixel(gx, gy, lay) {
    return [lay.boardOx + gx * lay.tileSize, lay.boardOy + gy * lay.tileSize];
  }

  cellCenter(gx, gy, lay) {
    const [px, py] = this.gridToPixel(gx, gy, lay);
    return [px + lay.tileSize / 2, py + lay.tileSize / 2];
  }

  appleCenterScreen(lay) {
    if (!this.apple) {
      return null;
    }
    return this.cellCenter(this.apple[0], this.apple[1], lay);
  }

  samplePolylineAtDistance(points, cum, distance) {
    if (!points.length) {
      return [0, 0];
    }
    const total = cum[cum.length - 1];
    if (total <= 0) {
      return points[points.length - 1];
    }
    const d = Math.max(0, Math.min(total, distance));
    for (let i = 0; i < cum.length - 1; i += 1) {
      const c0 = cum[i];
      const c1 = cum[i + 1];
      if (d <= c1) {
        const segLen = c1 - c0;
        if (segLen <= 1e-6) {
          return points[i + 1];
        }
        const t = (d - c0) / segLen;
        return lerpPt(points[i], points[i + 1], t);
      }
    }
    return points[points.length - 1];
  }

  segmentIndexAtArcDistance(cum, arcDistance) {
    if (cum.length < 2) {
      return 0;
    }
    const d = Math.max(0, Math.min(cum[cum.length - 1], arcDistance));
    for (let i = 0; i < cum.length - 1; i += 1) {
      if (d <= cum[i + 1]) {
        return i;
      }
    }
    return cum.length - 2;
  }

  bulgeDecaySegmentsForLength() {
    return Math.max(4, Math.min(C.BULGE_FADE_SEGMENTS_CAP, this.snake.length));
  }

  spawnBulge() {
    this.bulges.push({
      distPx: 0,
      startScale: C.BULGE_START_SCALE,
      endScale: C.BULGE_MIN_END_SCALE,
      decaySegments: this.bulgeDecaySegmentsForLength(),
      delayFrames: C.BULGE_SPAWN_DELAY_FRAMES,
      released: false,
      holdHeadUntilTick: false,
    });
  }

  bulgeHeadspaceSpeedPx(tileSize) {
    return (1 + C.BULGE_TRAVEL_SEG_PER_TICK) * tileSize;
  }

  advanceGrowthReveal(movedTiles) {
    const moved = Math.max(0, Number(movedTiles) || 0);
    if (moved <= 0 || this.growthHiddenTiles <= 0) {
      return;
    }
    const reveal = moved * C.GROWTH_REVEAL_TILES_PER_TILE;
    this.growthHiddenTiles = Math.max(0, this.growthHiddenTiles - reveal);
  }

  radiusForSegmentFromHead(segFromHead, baseR) {
    const safeBaseR = Math.max(1, Number(baseR) || 1);
    const minR = Math.max(1, safeBaseR * C.TAIL_MIN_RADIUS_FACTOR);
    const taperSeg = Math.max(0, segFromHead - (C.START_SNAKE_SEGMENTS - 1));
    const taperSpanSegments = Math.max(1e-6, (safeBaseR - minR) / C.SEGMENT_SHRINK_PER_SEG);
    const taperProgress = Math.max(0, Math.min(1, taperSeg / taperSpanSegments));
    return Math.max(minR, lerp(safeBaseR, minR, smoothstep(taperProgress)));
  }

  radiusForArcFromHeadPx(arcFromHeadPx, tileSize, baseR) {
    const safeTileSize = Math.max(1, Number(tileSize) || 1);
    const segFromHead = Math.max(0, (Number(arcFromHeadPx) || 0) / safeTileSize);
    return this.radiusForSegmentFromHead(segFromHead, baseR);
  }

  headBodyAngle(headC, neckC, fallbackAngle) {
    if (!headC || !neckC) {
      return fallbackAngle;
    }
    const vx = headC[0] - neckC[0];
    const vy = headC[1] - neckC[1];
    if (vecLen(vx, vy) <= 1e-6) {
      return fallbackAngle;
    }
    return Math.atan2(vy, vx) * 180 / Math.PI;
  }

  segmentAfterHeadAngle(segments, fallbackAngle) {
    if (segments.length >= 3) {
      return this.headBodyAngle(segments[1], segments[2], fallbackAngle);
    }
    if (segments.length >= 2) {
      return this.headBodyAngle(segments[0], segments[1], fallbackAngle);
    }
    return fallbackAngle;
  }

  faceAngleFromHeadPath(points, fallbackAngle) {
    if (points.length < 2) {
      return fallbackAngle;
    }
    const [headX, headY] = points[points.length - 1];
    for (let i = points.length - 2; i >= 0; i -= 1) {
      const [prevX, prevY] = points[i];
      const vx = headX - prevX;
      const vy = headY - prevY;
      if (vecLen(vx, vy) <= 1e-6) {
        continue;
      }
      if (Math.abs(vx) >= Math.abs(vy)) {
        return this.dirToAngle(vx >= 0 ? RIGHT : LEFT);
      }
      return this.dirToAngle(vy >= 0 ? DOWN : UP);
    }
    return fallbackAngle;
  }

  facePairCenter(headC, faceAngle, lay) {
    const [dx, dy] = this.angleVec(faceAngle);
    const [perpX, perpY] = [-dy, dx];
    return [
      headC[0] + dx * lay.tileSize * C.EYE_CENTER_FWD + perpX * lay.tileSize * C.EYE_CENTER_SIDE,
      headC[1] + dy * lay.tileSize * C.EYE_CENTER_FWD + perpY * lay.tileSize * C.EYE_CENTER_SIDE,
    ];
  }

  currentHeadAngle(nowMs) {
    if (nowMs >= this.turnEndMs) {
      this.headAngleDeg = this.turnToDeg;
      return this.headAngleDeg;
    }
    if (nowMs <= this.turnStartMs) {
      return this.turnFromDeg;
    }
    const duration = Math.max(1, this.turnEndMs - this.turnStartMs);
    const t = Math.max(0, Math.min(1, (nowMs - this.turnStartMs) / duration));
    const eased = t * t * (3 - 2 * t);
    this.headAngleDeg = angleLerpShortest(this.turnFromDeg, this.turnToDeg, eased);
    return this.headAngleDeg;
  }

  startHeadTurn(newDir, nowMs) {
    this.turnFromDeg = this.currentHeadAngle(nowMs);
    this.turnToDeg = this.dirToAngle(newDir);
    this.turnStartMs = nowMs;
    const arcTiles = 0.45 * 2.0;
    const turnMs = Math.trunc((arcTiles * 1000) / Math.max(0.01, this.moveSpeed || (1000 / C.TICK_RATE)));
    this.turnEndMs = nowMs + Math.max(50, turnMs);
  }

  buildTransitionPoints(lay, segments, prevHead, prevTail, progress) {
    if (segments.length < 2) {
      return { points: [], headC: null };
    }
    const t = Math.max(0, Math.min(1, progress));
    const cc = (gx, gy) => this.cellCenter(gx, gy, lay);
    const ghostTip = lerpPt(cc(prevTail[0], prevTail[1]), cc(segments[segments.length - 1][0], segments[segments.length - 1][1]), t);
    const headC = lerpPt(cc(prevHead[0], prevHead[1]), cc(segments[0][0], segments[0][1]), t);
    const points = [ghostTip];
    for (let i = segments.length - 1; i > 0; i -= 1) {
      points.push(cc(segments[i][0], segments[i][1]));
    }
    points.push(headC);
    return { points, headC };
  }

  rebuildBodyPath() {
    this.bodyPath = [];
    for (let i = this.snake.length - 1; i >= 0; i -= 1) {
      this.bodyPath.push(this.snake[i].map((value) => Number(value)));
    }
  }

  smoothPathCorners(points, radius) {
    if (points.length < 3) {
      return points;
    }
    const smoothed = [points[0]];
    for (let i = 1; i < points.length - 1; i += 1) {
      const A = points[i - 1];
      const B = points[i];
      const Cpt = points[i + 1];
      const ab = vecLen(B[0] - A[0], B[1] - A[1]);
      const bc = vecLen(Cpt[0] - B[0], Cpt[1] - B[1]);
      if (ab < 0.1 || bc < 0.1) {
        smoothed.push(B);
        continue;
      }
      const din = [(B[0] - A[0]) / ab, (B[1] - A[1]) / ab];
      const dout = [(Cpt[0] - B[0]) / bc, (Cpt[1] - B[1]) / bc];
      const dot = din[0] * dout[0] + din[1] * dout[1];
      if (Math.abs(dot) > 0.95) {
        smoothed.push(B);
        continue;
      }
      const off = Math.min(radius, ab * 0.48, bc * 0.48);
      if (off < 1) {
        smoothed.push(B);
        continue;
      }
      const p0 = [B[0] - din[0] * off, B[1] - din[1] * off];
      const p2 = [B[0] + dout[0] * off, B[1] + dout[1] * off];
      const arcSteps = 8;
      for (let j = 0; j <= arcSteps; j += 1) {
        const t = j / arcSteps;
        const mt = 1 - t;
        smoothed.push([
          mt * mt * p0[0] + 2 * mt * t * B[0] + t * t * p2[0],
          mt * mt * p0[1] + 2 * mt * t * B[1] + t * t * p2[1],
        ]);
      }
    }
    smoothed.push(points[points.length - 1]);
    return smoothed;
  }

  buildContinuousBodyPath(lay) {
    const segmentCount = this.snake.length;
    if (segmentCount < 2) {
      return { points: [], headC: null };
    }
    const headC = [
      lay.boardOx + this.headFloat[0] * lay.tileSize + lay.tileSize / 2,
      lay.boardOy + this.headFloat[1] * lay.tileSize + lay.tileSize / 2,
    ];
    const back = [headC];
    for (let i = this.bodyPath.length - 1; i >= 0; i -= 1) {
      const [bx, by] = this.bodyPath[i];
      back.push([
        lay.boardOx + bx * lay.tileSize + lay.tileSize / 2,
        lay.boardOy + by * lay.tileSize + lay.tileSize / 2,
      ]);
    }
    if (back.length >= 2) {
      const [lx, ly] = back[back.length - 1];
      const [px, py] = back[back.length - 2];
      back.push([lx + (lx - px), ly + (ly - py)]);
    }
    const cum = [0];
    for (let i = 1; i < back.length; i += 1) {
      cum.push(cum[cum.length - 1] + vecLen(back[i][0] - back[i - 1][0], back[i][1] - back[i - 1][1]));
    }
    const totalPath = cum[cum.length - 1];
    const visibleLenTiles = Math.max(0, (segmentCount - 1) - this.growthHiddenTiles);
    const bodyLen = Math.min(visibleLenTiles * lay.tileSize, totalPath);
    if (bodyLen <= 0) {
      return { points: [headC], headC };
    }
    const tailPx = this.samplePolylineAtDistance(back, cum, bodyLen);
    const interior = [];
    for (let i = 1; i < back.length - 1; i += 1) {
      if (cum[i] > 0 && cum[i] < bodyLen) {
        interior.push(i);
      }
    }
    const points = [tailPx];
    for (let i = interior.length - 1; i >= 0; i -= 1) {
      points.push(back[interior[i]]);
    }
    points.push(headC);
    const filtered = [points[0]];
    for (let i = 1; i < points.length; i += 1) {
      if (vecLen(points[i][0] - filtered[filtered.length - 1][0], points[i][1] - filtered[filtered.length - 1][1]) > 0.5) {
        filtered.push(points[i]);
      }
    }
    if (filtered[filtered.length - 1] !== points[points.length - 1]) {
      filtered.push(points[points.length - 1]);
    }
    return {
      points: this.smoothPathCorners(filtered, lay.tileSize * 0.45),
      headC,
    };
  }

  timedAnimationFrameIdx(nowMs, { startMs, playMs, frameCount, freezeFinal }) {
    if (startMs == null || frameCount <= 0) {
      return null;
    }
    if (frameCount === 1) {
      if (!freezeFinal && nowMs >= startMs + Math.max(0, playMs)) {
        return null;
      }
      return 0;
    }
    if (playMs <= 0) {
      return freezeFinal ? frameCount - 1 : null;
    }
    const elapsed = Math.max(0, nowMs - startMs);
    if (elapsed >= playMs) {
      return freezeFinal ? frameCount - 1 : null;
    }
    return Math.min(frameCount - 1, Math.floor(elapsed / (playMs / frameCount)));
  }

  buildCollisionEffectState(nowMs, direction, anchorPx) {
    const extraRot = (direction === UP || direction === DOWN) ? C.COLLISION_EFFECT_EXTRA_ROT_DEG : 0;
    return {
      startMs: nowMs,
      direction: direction.slice(),
      angleDeg: this.dirToAngle(direction) + extraRot,
      anchorPx,
    };
  }

  collisionEffectAnchorPx(effect, headC, lay) {
    if (effect.anchorPx) {
      return effect.anchorPx;
    }
    if (!headC) {
      return [null, null];
    }
    return [
      headC[0] + effect.direction[0] * lay.tileSize * C.COLLISION_EFFECT_ANCHOR_FWD,
      headC[1] + effect.direction[1] * lay.tileSize * C.COLLISION_EFFECT_ANCHOR_FWD,
    ];
  }

  headMotionProgress() {
    if (this.gameState !== "playing" || !this.headFloat || !this.lastHeadCell) {
      return 0;
    }
    const [dx, dy] = this.direction;
    let progress = 0;
    if (dx > 0) {
      progress = this.headFloat[0] - this.lastHeadCell[0];
    } else if (dx < 0) {
      progress = this.lastHeadCell[0] - this.headFloat[0];
    } else if (dy > 0) {
      progress = this.headFloat[1] - this.lastHeadCell[1];
    } else {
      progress = this.lastHeadCell[1] - this.headFloat[1];
    }
    return Math.max(0, Math.min(1, progress));
  }

  collisionShakeOffsetPx(nowMs, lay) {
    if (nowMs >= this.collisionShakeEndMs) {
      return [0, 0];
    }
    const duration = Math.max(1, this.collisionShakeEndMs - this.collisionShakeStartMs);
    const t = Math.max(0, Math.min(1, (nowMs - this.collisionShakeStartMs) / duration));
    const decay = (1 - t) * (1 - t);
    const amp = lay.tileSize * C.COLLISION_SHAKE_AMPLITUDE_TILES * decay;
    const phase = Math.PI * 2 * t;
    return [
      Math.sin(phase * C.COLLISION_SHAKE_X_CYCLES + 0.35) * amp,
      Math.sin(phase * C.COLLISION_SHAKE_Y_CYCLES + 1.10) * amp * 0.8,
    ];
  }

  collisionImpactHead(kind, attemptedHead) {
    if (kind === "border") {
      return [
        attemptedHead[0] - this.direction[0] * C.BORDER_CONTACT_INSET_TILES,
        attemptedHead[1] - this.direction[1] * C.BORDER_CONTACT_INSET_TILES,
      ];
    }
    if (kind === "self") {
      return [
        attemptedHead[0] - this.direction[0] * 0.6,
        attemptedHead[1] - this.direction[1] * 0.6,
      ];
    }
    return attemptedHead.slice();
  }

  resetRecoilPathHistory() {
    this.recoilPathHistory = [...this.snake].reverse().map((cell) => cell.slice());
    this.trimRecoilPathHistory();
  }

  trimRecoilPathHistory() {
    const keepCells = Math.max(2, this.snake.length + C.COLLISION_PATH_EXTRA_CELLS);
    while (this.recoilPathHistory.length > keepCells) {
      this.recoilPathHistory.shift();
    }
  }

  snapshotRecoilPathTiles() {
    const retracePath = [];
    for (let i = this.bodyPath.length - 1; i >= 0; i -= 1) {
      retracePath.push(this.bodyPath[i].slice());
    }
    const historyPath = [...this.recoilPathHistory].reverse();
    const tailRef = retracePath.length ? retracePath[retracePath.length - 1] : null;
    let startIdx = 0;
    if (tailRef) {
      startIdx = historyPath.findIndex(
        ([hx, hy]) => Math.abs(hx - tailRef[0]) <= 1e-6 && Math.abs(hy - tailRef[1]) <= 1e-6,
      );
      startIdx = startIdx >= 0 ? startIdx + 1 : 0;
    }
    retracePath.push(...historyPath.slice(startIdx).map(([hx, hy]) => [Number(hx), Number(hy)]));
    if (!retracePath.length) {
      retracePath.push(this.snake[0].map((value) => Number(value)));
    }
    const compact = [retracePath[0]];
    for (const point of retracePath.slice(1)) {
      if (vecLen(point[0] - compact[compact.length - 1][0], point[1] - compact[compact.length - 1][1]) > 1e-6) {
        compact.push(point);
      }
    }
    return compact;
  }

  recordRecoilPathHead(newHead) {
    this.recoilPathHistory.push(newHead.slice());
    this.trimRecoilPathHistory();
  }

  buildRecoilPoints(lay, impactHeadTile, retracePathTiles, visibleLength, progress, tailTrimPx = 0) {
    const clamped = Math.max(0, Math.min(1, progress));
    if (!retracePathTiles.length) {
      return { points: [], headC: null, headAngle: this.dirToAngle(this.direction) };
    }
    const safeVisible = Math.max(1, Math.min(visibleLength, retracePathTiles.length));
    const impactHeadPx = this.cellCenter(impactHeadTile[0], impactHeadTile[1], lay);
    const liveHeadPx = this.cellCenter(retracePathTiles[0][0], retracePathTiles[0][1], lay);
    const contactDistPx = vecLen(liveHeadPx[0] - impactHeadPx[0], liveHeadPx[1] - impactHeadPx[1]);
    const tailExtensionTiles = C.COLLISION_BACKUP_TILES;
    const pathGrid = [impactHeadTile.slice(), ...retracePathTiles.map((cell) => cell.slice())];
    let tailExtension;
    if (retracePathTiles.length >= 2) {
      const [tailX, tailY] = retracePathTiles[retracePathTiles.length - 1];
      const [prevX, prevY] = retracePathTiles[retracePathTiles.length - 2];
      tailExtension = [
        tailX + (tailX - prevX) * tailExtensionTiles,
        tailY + (tailY - prevY) * tailExtensionTiles,
      ];
    } else {
      tailExtension = retracePathTiles[retracePathTiles.length - 1].slice();
    }
    pathGrid.push(tailExtension);
    const pathPx = pathGrid.map(([gx, gy]) => this.cellCenter(gx, gy, lay));
    const cum = [0];
    for (let i = 1; i < pathPx.length; i += 1) {
      cum.push(cum[cum.length - 1] + vecLen(pathPx[i][0] - pathPx[i - 1][0], pathPx[i][1] - pathPx[i - 1][1]));
    }
    const visibleTailIdx = Math.min(cum.length - 2, safeVisible);
    const maxTailTrimPx = Math.max(0, cum[visibleTailIdx] - 1);
    const bodyLen = Math.max(0, cum[visibleTailIdx] - Math.min(maxTailTrimPx, Math.max(0, tailTrimPx)));
    const maxHeadDist = contactDistPx + lay.tileSize * C.COLLISION_BACKUP_TILES;
    const headDist = (1 - clamped) * maxHeadDist;
    const tailDist = Math.min(cum[cum.length - 1], headDist + bodyLen);
    const headC = this.samplePolylineAtDistance(pathPx, cum, headDist);
    const ghostTip = this.samplePolylineAtDistance(pathPx, cum, tailDist);
    const points = [ghostTip];
    for (let i = pathPx.length - 1; i >= 0; i -= 1) {
      if (headDist < cum[i] && cum[i] < tailDist) {
        points.push(pathPx[i]);
      }
    }
    points.push(headC);
    const segIdx = this.segmentIndexAtArcDistance(cum, headDist);
    const p0 = pathPx[segIdx];
    const p1 = pathPx[segIdx + 1];
    const headAngle = Math.atan2(p0[1] - p1[1], p0[0] - p1[0]) * 180 / Math.PI;
    if (points.length >= 3) {
      const smoothed = this.smoothPathCorners(points, lay.tileSize * 0.45);
      return {
        points: smoothed,
        headC: smoothed[smoothed.length - 1],
        headAngle,
      };
    }
    return { points, headC, headAngle };
  }

  buildFrozenCollisionPose() {
    if (!this.collisionRecoil) {
      return null;
    }
    const recoil = this.collisionRecoil;
    return {
      impactHead: recoil.impactHead.slice(),
      faceAngle: recoil.faceAngle,
      recoilFaceFromAngle: recoil.recoilFaceFromAngle,
      recoilFaceToAngle: recoil.recoilFaceToAngle,
      impactFaceAngle: recoil.impactFaceAngle,
      twitchFaceAngle: recoil.twitchFaceAngle,
      retracePathTiles: recoil.retracePathTiles.map((cell) => cell.slice()),
      visibleLength: recoil.visibleLength,
      progress: 0,
    };
  }

  collisionRetraceProgress(nowMs) {
    if (!this.collisionRecoil) {
      return 0;
    }
    const recoil = this.collisionRecoil;
    if (nowMs <= recoil.holdUntilMs) {
      return 1;
    }
    const duration = Math.max(1, recoil.retraceEndMs - recoil.holdUntilMs);
    const t = Math.max(0, Math.min(1, (nowMs - recoil.holdUntilMs) / duration));
    return 1 - easeOutQuad(t);
  }

  collisionTailTrimPx(nowMs, lay) {
    if (!this.collisionRecoil) {
      return 0;
    }
    const recoil = this.collisionRecoil;
    const maxTrimPx = lay.tileSize * C.COLLISION_TAIL_INSET_TILES;
    if (nowMs <= recoil.holdUntilMs) {
      const introDuration = Math.max(1, recoil.holdUntilMs - recoil.startMs);
      const t = Math.max(0, Math.min(1, (nowMs - recoil.startMs) / introDuration));
      return maxTrimPx * smoothstep(t);
    }
    if (nowMs >= recoil.retraceEndMs) {
      return 0;
    }
    const recoilDuration = Math.max(1, recoil.retraceEndMs - recoil.holdUntilMs);
    const t = Math.max(0, Math.min(1, (nowMs - recoil.holdUntilMs) / recoilDuration));
    return maxTrimPx * (1 - smoothstep(t));
  }

  phaseFrameIdx(startFrame, endFrame, elapsedMs, durationMs) {
    if (endFrame <= startFrame) {
      return startFrame;
    }
    const span = endFrame - startFrame;
    if (durationMs <= 0) {
      return endFrame - 1;
    }
    const t = Math.max(0, Math.min(0.999999, elapsedMs / durationMs));
    return startFrame + Math.min(span - 1, Math.floor(t * span));
  }

  collisionEffectFrameIdx(nowMs) {
    if (!this.collisionEffect || !this.collisionEffectFrames.length) {
      return null;
    }
    const totalVisibleMs = C.DEATH_FACE_COLLISION_INTRO_MS + C.DEATH_FACE_RECOIL_MS + C.DEATH_SCREEN_DELAY_MS;
    const elapsed = Math.max(0, nowMs - this.collisionEffect.startMs);
    if (elapsed >= totalVisibleMs) {
      return null;
    }
    const playMs = Math.max(1, Math.round(totalVisibleMs / Math.max(0.01, C.COLLISION_EFFECT_SPEED_MULT)));
    return this.timedAnimationFrameIdx(nowMs, {
      startMs: this.collisionEffect.startMs,
      playMs,
      frameCount: this.collisionEffectFrames.length,
      freezeFinal: false,
    });
  }

  deathFaceFrameIdx(nowMs) {
    if (!this.deathFaceAnim || !this.deathFaceFrames.length) {
      return null;
    }
    const frameCount = this.deathFaceFrames.length;
    const recoilStart = Math.max(1, Math.min(C.DEATH_FACE_RECOIL_START_FRAME, frameCount - 1));
    const twitchStart = Math.max(recoilStart + 1, Math.min(C.DEATH_FACE_TWITCH_START_FRAME, frameCount - 1));
    const holdEndMs = this.deathFaceAnim.holdEndMs ?? this.deathFaceAnim.startMs;
    const retraceEndMs = this.deathFaceAnim.retraceEndMs ?? holdEndMs;
    if (nowMs < holdEndMs) {
      return this.phaseFrameIdx(0, recoilStart, nowMs - this.deathFaceAnim.startMs, holdEndMs - this.deathFaceAnim.startMs);
    }
    if (nowMs < retraceEndMs) {
      return this.phaseFrameIdx(recoilStart, twitchStart, nowMs - holdEndMs, retraceEndMs - holdEndMs);
    }
    const loopCount = frameCount - twitchStart;
    if (loopCount <= 0) {
      return frameCount - 1;
    }
    const loopElapsed = Math.max(0, nowMs - retraceEndMs);
    return twitchStart + (Math.floor(loopElapsed / Math.max(1, C.DEATH_FACE_TWITCH_FRAME_MS)) % loopCount);
  }

  deathFaceAngleForFrame(frameIdx, progress, faceAngle, recoilFaceFromAngle, recoilFaceToAngle, impactFaceAngle, twitchFaceAngle) {
    if (faceAngle != null) {
      return faceAngle;
    }
    if (recoilFaceFromAngle != null && recoilFaceToAngle != null) {
      return angleLerpShortest(recoilFaceFromAngle, recoilFaceToAngle, progress);
    }
    if (twitchFaceAngle != null) {
      return twitchFaceAngle;
    }
    if (impactFaceAngle != null) {
      return impactFaceAngle;
    }
    return 0;
  }

  scheduleNextTongueRattle(nowMs) {
    this.tongueNextRattleMs = nowMs + Math.round(
      triangleSample(C.TONGUE_RATTLE_MIN_SEC, C.TONGUE_RATTLE_MAX_SEC, C.TONGUE_RATTLE_MODE_SEC) * 1000,
    );
  }

  cancelTongueRattle(nowMs, { reschedule }) {
    this.tongueAnimActive = false;
    this.tongueAnimPhase = 0;
    this.tongueAnimDir = 1;
    this.tongueFrameIdx = 0;
    this.tongueLastUpdateMs = nowMs;
    if (reschedule) {
      this.scheduleNextTongueRattle(nowMs);
    }
  }

  scheduleNextEyeBlink(nowMs) {
    this.eyeNextBlinkMs = nowMs + Math.round(
      triangleSample(C.EYE_BLINK_MIN_SEC, C.EYE_BLINK_MAX_SEC, C.EYE_BLINK_MODE_SEC) * 1000,
    );
  }

  cancelEyeBlink(nowMs, { reschedule }) {
    this.eyeBlinkActive = false;
    this.eyeFrameIdx = 0;
    this.eyeLastUpdateMs = nowMs;
    if (reschedule) {
      this.scheduleNextEyeBlink(nowMs);
    }
  }

  tongueIsAllowed() {
    return (
      this.gameState === "playing" &&
      this.mouthPhase <= 0 &&
      !this.mouthTargetOpen &&
      this.tongueFrames.length > 0
    );
  }

  updateTongueAnim(nowMs) {
    if (this.tongueFrames.length <= 1) {
      this.cancelTongueRattle(nowMs, { reschedule: this.gameState === "playing" });
      return;
    }
    if (!this.tongueIsAllowed()) {
      this.cancelTongueRattle(nowMs, { reschedule: this.gameState === "playing" });
      return;
    }
    if (!this.tongueAnimActive) {
      if (nowMs < this.tongueNextRattleMs) {
        return;
      }
      this.tongueAnimActive = true;
      this.tongueAnimPhase = 0;
      this.tongueAnimDir = 1;
      this.tongueFrameIdx = 1;
      this.tongueLastUpdateMs = nowMs;
      return;
    }
    const frameMs = Math.max(1, Math.round(C.TONGUE_FRAME_SEC * 1000));
    const elapsed = nowMs - this.tongueLastUpdateMs;
    if (elapsed < frameMs) {
      return;
    }
    const steps = Math.floor(elapsed / frameMs);
    this.tongueLastUpdateMs += steps * frameMs;
    const lastIdx = this.tongueFrames.length - 1;
    for (let i = 0; i < steps; i += 1) {
      this.tongueAnimPhase += this.tongueAnimDir;
      const nextIdx = this.tongueFrameIdx + this.tongueAnimDir;
      if (nextIdx >= lastIdx) {
        this.tongueFrameIdx = lastIdx;
        this.tongueAnimDir = -1;
      } else if (nextIdx <= 0) {
        this.cancelTongueRattle(nowMs, { reschedule: true });
        break;
      } else {
        this.tongueFrameIdx = nextIdx;
      }
    }
  }

  updateEyeBlink(nowMs) {
    if (this.eyeFrames.length <= 1) {
      this.cancelEyeBlink(nowMs, { reschedule: this.gameState !== "dead" });
      return;
    }
    if (this.gameState === "dead") {
      this.cancelEyeBlink(nowMs, { reschedule: false });
      return;
    }
    if (!this.eyeBlinkActive) {
      if (nowMs < this.eyeNextBlinkMs) {
        return;
      }
      this.eyeBlinkActive = true;
      this.eyeFrameIdx = 1;
      this.eyeLastUpdateMs = nowMs;
      return;
    }
    const frameMs = Math.max(1, Math.round(C.EYE_BLINK_FRAME_SEC * 1000));
    const elapsed = nowMs - this.eyeLastUpdateMs;
    if (elapsed < frameMs) {
      return;
    }
    const steps = Math.floor(elapsed / frameMs);
    this.eyeLastUpdateMs += steps * frameMs;
    const lastIdx = this.eyeFrames.length - 1;
    const nextIdx = this.eyeFrameIdx + steps;
    if (nextIdx > lastIdx) {
      this.cancelEyeBlink(nowMs, { reschedule: true });
      return;
    }
    this.eyeFrameIdx = nextIdx;
  }

  isHeadNearAppleTiles() {
    if (!this.apple || !this.snake.length) {
      return false;
    }
    const [hx, hy] = this.snake[0];
    const [ax, ay] = this.apple;
    const dist = Math.max(Math.abs(hx - ax), Math.abs(hy - ay));
    return dist > 0 && dist <= C.MOUTH_TRIGGER_RADIUS_TILES;
  }

  mouthFrameFromPhase(phase, opening) {
    const p = Math.max(0, Math.min(1, phase));
    if (p <= 0 || !this.mouthFrames.length || !this.mouthFrameOpenAmounts.length) {
      return 0;
    }
    const peakIdx = Math.max(0, Math.min(this.mouthPeakFrameIdx, this.mouthFrameOpenAmounts.length - 1));
    let candidates;
    let tieBreak;
    if (opening) {
      candidates = peakIdx <= 0 ? [...Array(this.mouthFrameOpenAmounts.length - 1).keys()].map((v) => v + 1) : [...Array(peakIdx).keys()].map((v) => v + 1);
      tieBreak = (i) => i;
    } else {
      candidates = [];
      for (let i = peakIdx; i < this.mouthFrameOpenAmounts.length; i += 1) {
        candidates.push(i);
      }
      if (!candidates.includes(0)) {
        candidates.push(0);
      }
      tieBreak = (i) => -i;
    }
    if (!candidates.length) {
      return 0;
    }
    return candidates.reduce((best, idx) => {
      const bestScore = Math.abs(this.mouthFrameOpenAmounts[best] - p);
      const nextScore = Math.abs(this.mouthFrameOpenAmounts[idx] - p);
      if (nextScore < bestScore) {
        return idx;
      }
      if (nextScore === bestScore && tieBreak(idx) < tieBreak(best)) {
        return idx;
      }
      return best;
    }, candidates[0]);
  }

  updateMouthAnim(nowMs, nearApple) {
    if (this.gameState !== "playing") {
      this.mouthTargetOpen = false;
      this.mouthCloseDelayUntilMs = 0;
    } else if (nearApple) {
      this.mouthTargetOpen = true;
      this.mouthCloseDelayUntilMs = 0;
    } else if (this.mouthPhase > 0) {
      if (this.mouthCloseDelayUntilMs === 0) {
        this.mouthCloseDelayUntilMs = nowMs + Math.round(C.MOUTH_CLOSE_DELAY_SEC * 1000);
      }
      if (nowMs >= this.mouthCloseDelayUntilMs) {
        this.mouthTargetOpen = false;
      }
    } else {
      this.mouthTargetOpen = false;
      this.mouthCloseDelayUntilMs = 0;
    }
    const prevPhase = this.mouthPhase;
    const durationSec = Math.max(1e-6, C.MOUTH_OPEN_CLOSE_FRAMES / C.FPS);
    const dt = Math.max(0, (nowMs - this.mouthLastUpdateMs) / 1000);
    this.mouthLastUpdateMs = nowMs;
    const step = dt / durationSec;
    const target = this.mouthTargetOpen ? 1 : 0;
    if (this.mouthPhase < target) {
      this.mouthPhase = Math.min(target, this.mouthPhase + step);
    } else if (this.mouthPhase > target) {
      this.mouthPhase = Math.max(target, this.mouthPhase - step);
    }
    const opening = this.mouthTargetOpen || this.mouthPhase >= prevPhase;
    this.mouthFrameIdx = this.mouthFrameFromPhase(this.mouthPhase, opening);
  }

  startWaitingRun(startDir) {
    if (startDir[0] === -this.direction[0] && startDir[1] === -this.direction[1]) {
      return false;
    }
    const nowMs = this.now();
    this.showWaitingStartCue = false;
    this.gameState = "playing";
    this.lastFrameMs = nowMs;
    this.direction = startDir.slice();
    this.nextDir = startDir.slice();
    this.startMoveLocked = true;
    this.prevDirection = startDir.slice();
    this.headAngleDeg = this.dirToAngle(startDir);
    this.turnFromDeg = this.headAngleDeg;
    this.turnToDeg = this.headAngleDeg;
    this.turnStartMs = nowMs;
    this.turnEndMs = nowMs;
    this.cancelTongueRattle(nowMs, { reschedule: true });
    return true;
  }

  handleStarterCardPlay() {
    if (this.starterCardContext === "death") {
      this.trophyUnlockedAfterRestart = true;
      this.newGame();
      return;
    }
    this.showWaitingCue();
  }

  enqueueDirection(newDir) {
    if (this.startMoveLocked) {
      return false;
    }
    const effectiveDir = this.inputQueue.length ? this.inputQueue[this.inputQueue.length - 1] : this.direction;
    if (newDir[0] === -effectiveDir[0] && newDir[1] === -effectiveDir[1]) {
      return false;
    }
    if (newDir[0] === effectiveDir[0] && newDir[1] === effectiveDir[1]) {
      return false;
    }
    if (this.inputQueue.length >= this.inputQueueMax) {
      return false;
    }
    this.inputQueue.push(newDir.slice());
    return true;
  }

  spawnApple() {
    const occupied = new Set(this.snake.map(([x, y]) => `${x},${y}`));
    const free = [];
    for (let y = 0; y < C.GRID_ROWS; y += 1) {
      for (let x = 0; x < C.GRID_COLS; x += 1) {
        if (!occupied.has(`${x},${y}`)) {
          free.push([x, y]);
        }
      }
    }
    this.apple = free.length ? free[Math.floor(Math.random() * free.length)] : null;
  }

  updateCollisionRecoil(nowMs) {
    if (this.gameState !== "colliding" || !this.collisionRecoil) {
      return;
    }
    if (nowMs < this.collisionRecoil.retraceEndMs) {
      return;
    }
    this.deathPose = this.buildFrozenCollisionPose();
    this.deathOverlayDelayUntilMs = this.collisionRecoil.overlayRevealMs;
    this.collisionRecoil = null;
    this.gameState = "dead";
    this.showWaitingStartCue = false;
    this.showStarterCard("death", this.score, this.deathOverlayDelayUntilMs);
  }

  beginCollisionRecoil(kind, impactHead) {
    const nowMs = this.now();
    const impact = this.collisionImpactHead(kind, impactHead);
    const faceAngle = this.currentHeadAngle(nowMs);
    const holdUntilMs = nowMs + C.DEATH_FACE_COLLISION_INTRO_MS;
    const retraceEndMs = holdUntilMs + C.DEATH_FACE_RECOIL_MS;
    this.playCollisionSound();
    this.gameState = "colliding";
    this.highScore = Math.max(this.highScore, this.score);
    this.saveHighScore();
    this.inputQueue = [];
    this.nextDir = this.direction.slice();
    const retracePath = this.snapshotRecoilPathTiles();
    this.collisionRecoil = {
      kind,
      startMs: nowMs,
      direction: this.direction.slice(),
      impactHead: impact,
      faceAngle,
      recoilFaceFromAngle: this.turnFromDeg,
      recoilFaceToAngle: faceAngle,
      impactFaceAngle: this.dirToAngle(this.direction),
      twitchFaceAngle: this.segmentAfterHeadAngle(this.snake, this.dirToAngle(this.direction)),
      retracePathTiles: retracePath,
      visibleLength: this.snake.length,
      holdUntilMs,
      retraceEndMs,
      overlayRevealMs: nowMs + C.DEATH_OVERLAY_REVEAL_MS,
    };
    const lay = this.layout();
    const impactHeadC = this.cellCenter(impact[0], impact[1], lay);
    const impactAnchorPx = [
      impactHeadC[0] + this.direction[0] * lay.tileSize * C.COLLISION_EFFECT_ANCHOR_FWD,
      impactHeadC[1] + this.direction[1] * lay.tileSize * C.COLLISION_EFFECT_ANCHOR_FWD,
    ];
    this.collisionEffect = this.buildCollisionEffectState(nowMs, this.direction, impactAnchorPx);
    this.deathFaceAnim = {
      startMs: nowMs,
      holdEndMs: holdUntilMs,
      retraceEndMs,
    };
    this.collisionShakeStartMs = nowMs;
    this.collisionShakeEndMs = nowMs + C.COLLISION_SHAKE_DURATION_MS;
  }

  tickIfDue(nowMs) {
    if (this.gameState !== "playing") {
      return;
    }
    const dtMs = Math.max(0, Math.min(nowMs - this.lastFrameMs, 50));
    this.lastFrameMs = nowMs;
    if (dtMs <= 0) {
      return;
    }
    this.advanceHead(this.moveSpeed * (dtMs / 1000));
  }

  advanceHead(dist) {
    if (dist <= 0 || this.gameState !== "playing") {
      return;
    }
    const startRemaining = dist;
    let remaining = dist;
    while (remaining > 1e-9 && this.gameState === "playing") {
      const [dx, dy] = this.direction;
      const nextCell = [this.lastHeadCell[0] + dx, this.lastHeadCell[1] + dy];
      let distToCenter = 0;
      if (dx > 0) {
        distToCenter = nextCell[0] - this.headFloat[0];
      } else if (dx < 0) {
        distToCenter = this.headFloat[0] - nextCell[0];
      } else if (dy > 0) {
        distToCenter = nextCell[1] - this.headFloat[1];
      } else {
        distToCenter = this.headFloat[1] - nextCell[1];
      }
      distToCenter = Math.max(0, distToCenter);

      let collisionKind = null;
      let collisionTriggerDistance = 0;
      if (nextCell[0] < 0 || nextCell[0] >= C.GRID_COLS || nextCell[1] < 0 || nextCell[1] >= C.GRID_ROWS) {
        collisionKind = "border";
        collisionTriggerDistance = C.BORDER_CONTACT_INSET_TILES;
      } else if (this.snake.slice(0, -1).some(([x, y]) => x === nextCell[0] && y === nextCell[1])) {
        collisionKind = "self";
        collisionTriggerDistance = 0.6;
      }
      if (collisionKind) {
        const distToCollision = Math.max(0, distToCenter - collisionTriggerDistance);
        if (remaining >= distToCollision) {
          this.headFloat[0] += dx * distToCollision;
          this.headFloat[1] += dy * distToCollision;
          this.beginCollisionRecoil(collisionKind, nextCell);
          break;
        }
      }

      const isAppleNext = !!this.apple && nextCell[0] === this.apple[0] && nextCell[1] === this.apple[1];
      if (isAppleNext) {
        const distToApple = Math.max(0, distToCenter - 0.7);
        if (remaining >= distToApple) {
          this.score += 1;
          this.highScore = Math.max(this.highScore, this.score);
          this.saveHighScore();
          this.tailDarkness = Math.min(1, this.tailDarkness + C.APPLE_DARKEN_STEP);
          this.playEatSound();
          this.spawnBulge();
          this.spawnApple();
          this.pendingGrowth += 1;
        }
      }

      if (remaining < distToCenter) {
        this.headFloat[0] += dx * remaining;
        this.headFloat[1] += dy * remaining;
        remaining = 0;
        break;
      }

      this.headFloat = [Number(nextCell[0]), Number(nextCell[1])];
      remaining -= distToCenter;
      if (dx !== 0) {
        this.headFloat[1] = Math.round(this.headFloat[1]);
      } else {
        this.headFloat[0] = Math.round(this.headFloat[0]);
      }
      const crossedPoint = this.headFloat.slice();
      this.bodyPath.push(crossedPoint);
      this.lastHeadCell = nextCell.slice();
      this.onEnterNewCell(nextCell);
      if (this.gameState !== "playing") {
        break;
      }
      if (this.inputQueue.length) {
        const queuedDir = this.inputQueue.shift();
        if (!(queuedDir[0] === -this.direction[0] && queuedDir[1] === -this.direction[1])) {
          this.prevDirection = this.direction.slice();
          this.direction = queuedDir.slice();
          this.nextDir = queuedDir.slice();
          this.startMoveLocked = false;
          this.lastTurnCell = nextCell.slice();
          this.startHeadTurn(this.direction, this.now());
          this.playTurnSound();
        }
      }
    }
    this.advanceGrowthReveal(Math.max(0, startRemaining - remaining));
  }

  onEnterNewCell(newCell) {
    if (newCell[0] < 0 || newCell[0] >= C.GRID_COLS || newCell[1] < 0 || newCell[1] >= C.GRID_ROWS) {
      this.beginCollisionRecoil("border", newCell);
      return;
    }
    if (this.snake.slice(0, -1).some(([x, y]) => x === newCell[0] && y === newCell[1])) {
      this.beginCollisionRecoil("self", newCell);
      return;
    }

    this.prevHead = this.snake[0].slice();
    this.prevTail = this.snake[this.snake.length - 1].slice();
    this.snake.unshift(newCell.slice());
    this.startMoveLocked = false;
    this.recordRecoilPathHead(newCell);

    if (this.pendingGrowth > 0) {
      this.pendingGrowth -= 1;
      this.growthHiddenTiles += 1;
    } else if (this.apple && newCell[0] === this.apple[0] && newCell[1] === this.apple[1]) {
      this.score += 1;
      this.highScore = Math.max(this.highScore, this.score);
      this.saveHighScore();
      this.tailDarkness = Math.min(1, this.tailDarkness + C.APPLE_DARKEN_STEP);
      this.playEatSound();
      this.spawnBulge();
      this.spawnApple();
    } else {
      this.snake.pop();
    }

    const bulgeStepPx = this.bulgeHeadspaceSpeedPx(this.layout().tileSize);
    for (const bulge of this.bulges) {
      if (bulge.delayFrames > 0 || !bulge.released) {
        continue;
      }
      if (bulge.holdHeadUntilTick) {
        bulge.holdHeadUntilTick = false;
        continue;
      }
      bulge.distPx += bulgeStepPx;
    }

    const maxPoints = this.snake.length * 3 + 20;
    while (this.bodyPath.length > maxPoints) {
      this.bodyPath.shift();
    }
  }

  pointInRect(rect, x, y) {
    return !!rect && x >= rect.x && y >= rect.y && x <= rect.x + rect.w && y <= rect.y + rect.h;
  }

  clientToCanvasPoint(event) {
    const rect = this.canvas.getBoundingClientRect();
    return {
      x: ((event.clientX - rect.left) / rect.width) * C.BASE_W,
      y: ((event.clientY - rect.top) / rect.height) * C.BASE_H,
    };
  }

  unlockAudio() {
    this.audioUnlocked = true;
  }

  stopAudio() {
    for (const item of this.activeSounds ?? []) {
      try {
        item.pause();
        item.currentTime = 0;
      } catch {
        // Ignore audio teardown issues.
      }
    }
    this.activeSounds = [];
  }

  playSound(def, { stack = true } = {}) {
    if (!def || !this.audioUnlocked || this.audioMuted) {
      return;
    }
    try {
      const audio = stack ? def.el.cloneNode() : def.el;
      audio.volume = this.audioMuted ? 0 : def.baseVolume;
      audio.currentTime = 0;
      audio.play().catch(() => {});
      if (!this.activeSounds) {
        this.activeSounds = [];
      }
      this.activeSounds.push(audio);
      audio.addEventListener("ended", () => {
        this.activeSounds = (this.activeSounds || []).filter((item) => item !== audio);
      }, { once: true });
    } catch {
      // Ignore browser audio issues.
    }
  }

  playTurnSound() {
    this.playSound(this.audio.turn, { stack: true });
  }

  playEatSound() {
    this.playSound(this.audio.eat, { stack: true });
  }

  playCollisionSound() {
    this.stopAudio();
    this.playSound(this.audio.collision, { stack: false });
  }

  toggleAudioMute() {
    this.audioMuted = !this.audioMuted;
    for (const def of Object.values(this.audio)) {
      if (def?.el) {
        def.el.volume = this.audioMuted ? 0 : def.baseVolume;
      }
    }
    if (this.audioMuted) {
      this.stopAudio();
    }
    this.draw();
  }

  toggleMaximized() {
    this.maximized = !this.maximized;
    this.page.classList.toggle("is-maximized", this.maximized);
    this.resizeCanvasBuffer();
  }

  updateCursor() {
    const interactive = [this.fsRect, this.volRect, this.playButtonRect];
    this.canvas.style.cursor = interactive.some((rect) => this.pointInRect(rect, this.pointer.x, this.pointer.y))
      ? "pointer"
      : "default";
  }

  handlePointerMove(event) {
    this.pointer = this.clientToCanvasPoint(event);
    this.updateCursor();
  }

  handleMouseDown(event) {
    this.unlockAudio();
    const point = this.clientToCanvasPoint(event);
    if (this.pointInRect(this.fsRect, point.x, point.y)) {
      this.toggleMaximized();
      return;
    }
    if (this.pointInRect(this.volRect, point.x, point.y)) {
      this.toggleAudioMute();
      return;
    }
    if (this.starterCardVisible && this.pointInRect(this.playButtonRect, point.x, point.y)) {
      this.handleStarterCardPlay();
      this.draw();
    }
  }

  handleKeyDown(event) {
    this.unlockAudio();
    if (event.code === "KeyF") {
      this.toggleMaximized();
      event.preventDefault();
      return;
    }
    if (
      event.code === "KeyR" &&
      this.gameState === "waiting" &&
      this.starterCardVisible &&
      this.starterCardContext === "launch"
    ) {
      this.showWaitingCue();
      this.draw();
      event.preventDefault();
      return;
    }
    if (event.code === "KeyR" && this.gameState === "dead") {
      this.trophyUnlockedAfterRestart = true;
      this.newGame();
      this.draw();
      event.preventDefault();
      return;
    }
    const dir = DIR_BY_KEY.get(event.code);
    if (dir && event.repeat) {
      // Match pygame key handling (no OS key-repeat direction spam).
      event.preventDefault();
      return;
    }
    if (this.starterCardVisible) {
      return;
    }
    if (!dir) {
      return;
    }
    event.preventDefault();
    if (this.gameState === "waiting") {
      this.startWaitingRun(dir);
      this.draw();
      return;
    }
    if (this.gameState === "playing") {
      this.enqueueDirection(dir);
    }
  }

  loop(nowMs) {
    if (!this.running) {
      return;
    }
    if (this.loaded) {
      this.refreshStarterCardVisibility(nowMs);
      this.tickIfDue(nowMs);
      this.updateCollisionRecoil(nowMs);
      this.draw(nowMs);
    } else {
      this.drawBootFrame();
    }
    requestAnimationFrame((ts) => this.loop(ts));
  }

  drawRotatedImage(image, centerX, centerY, pygameAngleDeg) {
    this.ctx.save();
    this.ctx.translate(centerX, centerY);
    // Match pygame.transform.rotate(...): browser canvas needs the inverse sign
    // to produce the same visual facing direction.
    this.ctx.rotate(-pygameAngleDeg * Math.PI / 180);
    this.ctx.drawImage(image, -image.width / 2, -image.height / 2);
    this.ctx.restore();
  }

  drawRoundedRect(x, y, w, h, radius, fillStyle) {
    const r = Math.min(radius, w / 2, h / 2);
    this.ctx.save();
    this.ctx.beginPath();
    this.ctx.moveTo(x + r, y);
    this.ctx.arcTo(x + w, y, x + w, y + h, r);
    this.ctx.arcTo(x + w, y + h, x, y + h, r);
    this.ctx.arcTo(x, y + h, x, y, r);
    this.ctx.arcTo(x, y, x + w, y, r);
    this.ctx.closePath();
    this.ctx.fillStyle = fillStyle;
    this.ctx.fill();
    this.ctx.restore();
  }

  drawHeader(lay) {
    const appleIcon = this.assets.apple_icon;
    const trophy = this.assets.trophy;
    const iconX = 12;
    const iconY = Math.floor((lay.headerH - appleIcon.height) / 2);
    this.ctx.drawImage(appleIcon, iconX, iconY);
    this.ctx.fillStyle = C.SCORE_COLOR;
    this.ctx.font = "bold 34px Arial";
    this.ctx.textBaseline = "middle";
    this.ctx.fillText(String(this.score), iconX + appleIcon.width + 8, lay.headerH / 2);
    const showTrophy = (
      this.trophyUnlockedAfterRestart &&
      this.highScore > 0 &&
      !(this.starterCardVisible && this.starterCardContext === "launch")
    );
    if (showTrophy) {
      const trophyX = iconX * 10;
      this.ctx.drawImage(trophy, trophyX, iconY);
      this.ctx.fillText(String(this.highScore), trophyX + trophy.width + 8, lay.headerH / 2);
    }
    const margin = 17;
    const gap = 16;
    const fullIcon = this.maximized ? this.assets.not_full_screen : this.assets.full_screen;
    const volumeIcon = this.audioMuted ? this.assets.volume_muted : this.assets.volume;
    const volX = lay.winW - margin - volumeIcon.width;
    const volY = Math.floor((lay.headerH - volumeIcon.height) / 2);
    const fsX = volX - gap - fullIcon.width;
    const fsY = Math.floor((lay.headerH - fullIcon.height) / 2);
    this.volRect = { x: volX, y: volY, w: volumeIcon.width, h: volumeIcon.height };
    this.fsRect = { x: fsX, y: fsY, w: fullIcon.width, h: fullIcon.height };
  }

  drawTiles(lay) {
    for (let row = 0; row < C.GRID_ROWS; row += 1) {
      for (let col = 0; col < C.GRID_COLS; col += 1) {
        const tile = (row + col) % 2 === 0 ? this.assets.tile_light : this.assets.tile_dark;
        const [px, py] = this.gridToPixel(col, row, lay);
        this.ctx.drawImage(tile, px, py, lay.tileSize, lay.tileSize);
      }
    }
  }

  drawApple(lay, nowMs) {
    if (!this.apple) {
      return;
    }
    const [px, py] = this.gridToPixel(this.apple[0], this.apple[1], lay);
    const source = this.assets.apple_board ?? this.assets.apple_icon;
    const pulse = this.gameState === "dead"
      ? this.applePulseFrozen
      : 1 + 0.2 * (0.5 + 0.5 * Math.cos((nowMs / 1000) * Math.PI * 2));
    this.applePulseFrozen = pulse;
    const newSize = Math.max(4, Math.round(source.width * pulse));
    const tileCx = px + lay.tileSize / 2;
    const tileCy = py + lay.tileSize / 2;
    const r = newSize / 2;
    const shadowW = r * 0.85 * pulse;
    const shadowH = Math.max(2, r * 0.18 * pulse);
    const yOff = r * 0.92;
    this.ctx.save();
    this.ctx.fillStyle = "rgba(0,0,0,0.2)";
    this.ctx.beginPath();
    this.ctx.ellipse(tileCx, tileCy + yOff, shadowW, shadowH, 0, 0, Math.PI * 2);
    this.ctx.fill();
    this.ctx.drawImage(source, tileCx - r, tileCy - r, newSize, newSize);
    this.ctx.restore();
  }

  drawSnakeBody(lay, points) {
    if (points.length < 2) {
      return null;
    }
    const r = lay.bodyR;
    const cum = [0];
    for (let i = 1; i < points.length; i += 1) {
      cum.push(cum[cum.length - 1] + vecLen(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]));
    }
    const total = cum[cum.length - 1];
    if (total < 1) {
      return null;
    }
    const shadowYOffset = Math.floor(r * C.SNAKE_SHADOW_YOFF_FACTOR);
    const shadowR = Math.max(1, Math.floor(r * C.SNAKE_SHADOW_RADIUS_FACTOR));
    const shadowCanvas = createCanvas(lay.boardW, lay.boardH + shadowYOffset + r + 4);
    const shadowCtx = shadowCanvas.getContext("2d");
    shadowCtx.strokeStyle = "rgba(0, 0, 0, 0.16)";
    shadowCtx.lineWidth = shadowR * 2;
    shadowCtx.lineCap = "round";
    shadowCtx.lineJoin = "round";
    shadowCtx.beginPath();
    shadowCtx.moveTo(points[0][0] - lay.boardOx, points[0][1] - lay.boardOy + shadowYOffset);
    for (let i = 1; i < points.length; i += 1) {
      shadowCtx.lineTo(points[i][0] - lay.boardOx, points[i][1] - lay.boardOy + shadowYOffset);
    }
    shadowCtx.stroke();
    this.ctx.drawImage(shadowCanvas, lay.boardOx, lay.boardOy);
    const headColor = C.SNAKE_HEAD_COLOR;
    const tailColor = mixColor(C.SNAKE_HEAD_COLOR, C.SNAKE_TAIL_DARK_MAX, this.tailDarkness);
    const stepPx = Math.max(1, r * 0.4);
    for (let seg = 0; seg < points.length - 1; seg += 1) {
      const p0 = points[seg];
      const p1 = points[seg + 1];
      const segLen = vecLen(p1[0] - p0[0], p1[1] - p0[1]);
      if (segLen < 0.1) {
        continue;
      }
      const steps = Math.max(1, Math.ceil(segLen / stepPx));
      let prevPt = p0;
      for (let s = 1; s <= steps; s += 1) {
        const localT = s / steps;
        const curPt = [p0[0] + (p1[0] - p0[0]) * localT, p0[1] + (p1[1] - p0[1]) * localT];
        const midT = (s - 0.5) / steps;
        const arcDist = cum[seg] + segLen * midT;
        const arcFromHead = total - arcDist;
        const segR = this.radiusForArcFromHeadPx(arcFromHead, lay.tileSize, r);
        const frac = Math.max(0, Math.min(1, arcDist / total));
        const color = mixColor(tailColor, headColor, frac);
        drawCapsule(this.ctx, rgba(color), prevPt, curPt, segR);
        prevPt = curPt;
      }
    }
    return { cum, total };
  }

  drawTongueFrame(headC, faceAngle, lay, frameIdx) {
    if (frameIdx <= 0 || frameIdx >= this.tongueFrames.length) {
      return;
    }
    const sprite = this.tongueFrames[frameIdx];
    const [dx, dy] = this.angleVec(faceAngle);
    const [perpX, perpY] = [-dy, dx];
    const baseX = headC[0] + dx * lay.tileSize * C.TONGUE_ANCHOR_FWD + perpX * lay.tileSize * C.TONGUE_ANCHOR_SIDE;
    const baseY = headC[1] + dy * lay.tileSize * C.TONGUE_ANCHOR_FWD + perpY * lay.tileSize * C.TONGUE_ANCHOR_SIDE;
    const tongueExtent = Math.max(sprite.width, sprite.height);
    const tx = baseX + dx * tongueExtent * C.TONGUE_BASE_OFFSET;
    const ty = baseY + dy * tongueExtent * C.TONGUE_BASE_OFFSET;
    const shadowYOffset = lay.tileSize * C.TONGUE_SHADOW_YOFF_FACTOR;
    const shadowLen = Math.max(2, sprite.width * C.TONGUE_SHADOW_SCALE);
    const shadowR = Math.max(1, sprite.height * 0.18);
    const shadowCanvas = createCanvas(shadowLen + shadowR * 2 + 6, shadowLen + shadowR * 2 + 6);
    const shadowCtx = shadowCanvas.getContext("2d");
    const origin = shadowCanvas.width / 2;
    drawCapsule(
      shadowCtx,
      "rgba(0, 0, 0, 0.16)",
      [origin + dx * shadowLen * 0.08, origin + shadowYOffset + dy * shadowLen * 0.08],
      [origin + dx * shadowLen * 0.92, origin + shadowYOffset + dy * shadowLen * 0.92],
      shadowR,
    );
    this.ctx.drawImage(shadowCanvas, baseX - origin, baseY - origin);
    this.drawRotatedImage(sprite, tx, ty, -faceAngle);
  }

  drawMouthFrame(headC, faceAngle, lay, frameIdx) {
    if (frameIdx <= 0 || frameIdx >= this.mouthFrames.length) {
      return;
    }
    const sprite = this.mouthFrames[frameIdx];
    const [dx, dy] = this.angleVec(faceAngle);
    const [perpX, perpY] = [-dy, dx];
    const mx = headC[0] + dx * lay.tileSize * C.MOUTH_ANCHOR_FWD + perpX * lay.tileSize * C.MOUTH_ANCHOR_SIDE;
    const my = headC[1] + dy * lay.tileSize * C.MOUTH_ANCHOR_FWD + perpY * lay.tileSize * C.MOUTH_ANCHOR_SIDE;
    const shadowW = Math.max(2, sprite.width * C.MOUTH_SHADOW_SCALE);
    const shadowH = Math.max(2, sprite.height * C.MOUTH_SHADOW_SCALE * 0.45);
    this.ctx.fillStyle = `rgba(0,0,0,${C.FACE_SHADOW_ALPHA / 255})`;
    this.ctx.beginPath();
    this.ctx.ellipse(mx, my + lay.tileSize * 0.08, shadowW / 2, shadowH / 2, 0, 0, Math.PI * 2);
    this.ctx.fill();
    this.drawRotatedImage(sprite, mx, my, -faceAngle);
  }

  drawEyes(headC, lay, faceAngle) {
    const [dx, dy] = this.angleVec(faceAngle);
    const [perpX, perpY] = [-dy, dx];
    const sprite = this.eyeFrames[Math.max(0, Math.min(this.eyeFrameIdx, this.eyeFrames.length - 1))];
    const pairC = this.facePairCenter(headC, faceAngle, lay);
    const sideOff = lay.tileSize * C.EYE_SEPARATION;
    const leftEye = [pairC[0] + perpX * sideOff, pairC[1] + perpY * sideOff];
    const rightEye = [pairC[0] - perpX * sideOff, pairC[1] - perpY * sideOff];
    if (sprite) {
      const shYOffset = Math.floor(lay.bodyR * 0.6 * C.EYE_SHADOW_SCALE);
      const shR = Math.max(1, Math.floor(lay.bodyR * 0.8 * C.EYE_SHADOW_SCALE));
      const surfW = Math.floor(lay.tileSize * 2.6);
      const surfH = Math.floor(lay.tileSize * 2.5);
      const ox = Math.floor(headC[0] - surfW / 2);
      const oy = Math.floor(headC[1] - surfH / 2);
      const shadowCanvas = createCanvas(surfW, surfH);
      const shadowCtx = shadowCanvas.getContext("2d");
      drawCapsule(
        shadowCtx,
        "rgba(0, 0, 0, 0.16)",
        [leftEye[0] - ox, leftEye[1] - oy + shYOffset],
        [rightEye[0] - ox, rightEye[1] - oy + shYOffset],
        shR,
      );
      shadowCtx.globalCompositeOperation = "destination-out";
      const neckC = [
        headC[0] - dx * lay.bodyR * 1.4,
        headC[1] - dy * lay.bodyR * 1.4,
      ];
      drawCapsule(
        shadowCtx,
        "rgba(0, 0, 0, 1)",
        [headC[0] - ox, headC[1] - oy],
        [neckC[0] - ox, neckC[1] - oy],
        lay.bodyR + 3,
      );
      drawCapsule(
        shadowCtx,
        "rgba(0, 0, 0, 1)",
        [headC[0] - ox, headC[1] - oy + shYOffset],
        [neckC[0] - ox, neckC[1] - oy + shYOffset],
        Math.max(1, Math.floor(lay.bodyR * 0.8)),
      );
      shadowCtx.globalCompositeOperation = "source-over";
      this.ctx.drawImage(shadowCanvas, ox, oy);
    }
    for (const [ex, ey] of [leftEye, rightEye]) {
      if (sprite) {
        this.drawRotatedImage(sprite, ex, ey, -faceAngle);
      }
    }
    const snoutX = headC[0] + dx * lay.tileSize * 0.34;
    const snoutY = headC[1] + dy * lay.tileSize * 0.34;
    const nostSide = lay.tileSize * 0.23;
    const nostFwd = lay.tileSize * -0.25;
    for (const sign of [1, -1]) {
      const nx = snoutX + dx * nostFwd + perpX * sign * nostSide;
      const ny = snoutY + dy * nostFwd + perpY * sign * nostSide;
      this.ctx.fillStyle = rgba(C.NOSE_COLOR);
      this.ctx.beginPath();
      this.ctx.arc(nx, ny, 1, 0, Math.PI * 2);
      this.ctx.fill();
    }
  }

  drawCollisionEffect(nowMs, headC, lay) {
    const frameIdx = this.collisionEffectFrameIdx(nowMs);
    if (frameIdx == null || !this.collisionEffect) {
      return;
    }
    const sprite = this.collisionEffectFrames[frameIdx];
    const [anchorX, anchorY] = this.collisionEffectAnchorPx(this.collisionEffect, headC, lay);
    if (anchorX == null || anchorY == null) {
      return;
    }
    this.drawRotatedImage(sprite, anchorX, anchorY, this.collisionEffect.angleDeg);
  }

  drawDeathFace(headC, progress, faceAngle, recoilFaceFromAngle, recoilFaceToAngle, impactFaceAngle, twitchFaceAngle, lay, nowMs) {
    const frameIdx = this.deathFaceFrameIdx(nowMs);
    if (frameIdx == null) {
      return;
    }
    const headAngle = this.deathFaceAngleForFrame(
      frameIdx,
      progress,
      faceAngle,
      recoilFaceFromAngle,
      recoilFaceToAngle,
      impactFaceAngle,
      twitchFaceAngle,
    );
    const sprite = this.deathFaceFrames[frameIdx];
    const [dx, dy] = this.angleVec(headAngle);
    const blendFrames = Math.max(1, C.DEATH_FACE_TWITCH_BLEND_FRAMES);
    const blendStart = Math.max(0, C.DEATH_FACE_TWITCH_START_FRAME - blendFrames);
    let blendT = 0;
    if (frameIdx <= blendStart) {
      blendT = 0;
    } else if (frameIdx >= C.DEATH_FACE_TWITCH_START_FRAME) {
      blendT = 1;
    } else {
      blendT = (frameIdx - blendStart) / Math.max(1, C.DEATH_FACE_TWITCH_START_FRAME - blendStart);
    }
    blendT = smoothstep(blendT);
    const anchorFwd = (
      C.DEATH_FACE_PRE_TWITCH_ANCHOR
      + (C.DEATH_FACE_TWITCH_ANCHOR - C.DEATH_FACE_PRE_TWITCH_ANCHOR) * blendT
      + C.DEATH_FACE_ANCHOR_BACK_SHIFT
    );
    const growthSpan = Math.max(1, C.DEATH_FACE_TWITCH_START_FRAME - C.DEATH_FACE_RECOIL_START_FRAME);
    let growthT = (frameIdx - C.DEATH_FACE_RECOIL_START_FRAME) / growthSpan;
    growthT = smoothstep(Math.max(0, Math.min(1, growthT)));
    const verticalLift = (Math.abs(dy) > Math.abs(dx) && dy < 0) ? lay.tileSize * C.DEATH_FACE_FRAME_LIFT * growthT : 0;
    const upCollisionYNudge = dy < 0 ? lay.tileSize * C.DEATH_FACE_UP_COLLISION_Y_NUDGE_TILES : 0;
    const targetX = headC[0] + dx * lay.tileSize * anchorFwd;
    const targetY = headC[1] + dy * lay.tileSize * anchorFwd + verticalLift + upCollisionYNudge;
    this.drawRotatedImage(sprite, targetX, targetY, -headAngle);
  }

  drawSnake(lay, progress, nowMs) {
    if (this.snake.length < 2) {
      return;
    }
    if (this.gameState === "colliding" && this.collisionRecoil) {
      const recoilProgress = this.collisionRetraceProgress(nowMs);
      const tailTrimPx = this.collisionTailTrimPx(nowMs, lay);
      const recoil = this.buildRecoilPoints(
        lay,
        this.collisionRecoil.impactHead,
        this.collisionRecoil.retracePathTiles,
        this.collisionRecoil.visibleLength,
        recoilProgress,
        tailTrimPx,
      );
      const body = this.drawSnakeBody(lay, recoil.points);
      if (!body || !recoil.headC) {
        return;
      }
      const faceAngle = this.faceAngleFromHeadPath(recoil.points, recoil.headAngle);
      this.drawCollisionEffect(nowMs, recoil.headC, lay);
      this.drawDeathFace(
        recoil.headC,
        recoilProgress,
        faceAngle,
        this.collisionRecoil.recoilFaceFromAngle,
        this.collisionRecoil.recoilFaceToAngle,
        this.collisionRecoil.impactFaceAngle,
        this.collisionRecoil.twitchFaceAngle,
        lay,
        nowMs,
      );
      return;
    }
    if (this.gameState === "dead" && this.deathPose) {
      const pose = this.buildRecoilPoints(
        lay,
        this.deathPose.impactHead,
        this.deathPose.retracePathTiles,
        this.deathPose.visibleLength,
        this.deathPose.progress,
      );
      const body = this.drawSnakeBody(lay, pose.points);
      if (!body || !pose.headC) {
        return;
      }
      const faceAngle = this.faceAngleFromHeadPath(pose.points, pose.headAngle);
      this.drawCollisionEffect(nowMs, pose.headC, lay);
      this.drawDeathFace(
        pose.headC,
        this.deathPose.progress,
        faceAngle,
        this.deathPose.recoilFaceFromAngle,
        this.deathPose.recoilFaceToAngle,
        this.deathPose.impactFaceAngle,
        this.deathPose.twitchFaceAngle,
        lay,
        nowMs,
      );
      return;
    }
    const transition = this.buildContinuousBodyPath(lay);
    if (!transition.headC || transition.points.length < 2) {
      return;
    }
    const headAngle = this.currentHeadAngle(nowMs);
    const body = this.drawSnakeBody(lay, transition.points);
    if (!body) {
      return;
    }
    // Mirror pygame runtime exactly: use the time-lerped head angle for face rendering.
    const faceAngle = headAngle;
    const headColor = C.SNAKE_HEAD_COLOR;
    const tailColor = mixColor(C.SNAKE_HEAD_COLOR, C.SNAKE_TAIL_DARK_MAX, this.tailDarkness);
    if (this.bulges.length) {
      const drawBulges = [];
      const bulgeSpeedPx = this.bulgeHeadspaceSpeedPx(lay.tileSize);
      for (const bulge of this.bulges) {
        if (bulge.delayFrames > 0) {
          bulge.delayFrames -= 1;
          drawBulges.push(bulge);
          continue;
        }
        let d;
        if (!bulge.released) {
          bulge.released = true;
          bulge.holdHeadUntilTick = true;
          d = 0;
        } else if (bulge.holdHeadUntilTick) {
          d = 0;
        } else {
          d = bulge.distPx + progress * bulgeSpeedPx;
        }
        const arcFromTail = body.total - d;
        const center = this.samplePolylineAtDistance(transition.points, body.cum, arcFromTail);
        const arcFromHead = body.total - arcFromTail;
        const localR = this.radiusForArcFromHeadPx(arcFromHead, lay.tileSize, lay.bodyR);
        const decayPx = Math.max(1, bulge.decaySegments * lay.tileSize);
        const t = Math.max(0, Math.min(1, d / decayPx));
        const scale = lerp(bulge.startScale, bulge.endScale, smoothstep(t));
        const br = Math.max(1, localR * scale);
        const bulgeFrac = Math.max(0, Math.min(1, arcFromTail / body.total));
        this.ctx.fillStyle = rgba(mixColor(tailColor, headColor, bulgeFrac));
        this.ctx.beginPath();
        this.ctx.arc(center[0], center[1], br, 0, Math.PI * 2);
        this.ctx.fill();
        if (d < body.total + lay.bodyR && t < C.BULGE_END_HIDE_T) {
          drawBulges.push(bulge);
        }
      }
      this.bulges = drawBulges;
    }
    const nearApple = this.isHeadNearAppleTiles();
    this.updateMouthAnim(nowMs, nearApple);
    this.updateTongueAnim(nowMs);
    if (this.tongueAnimActive) {
      this.drawTongueFrame(transition.headC, faceAngle, lay, this.tongueFrameIdx);
    }
    this.drawMouthFrame(transition.headC, faceAngle, lay, this.mouthFrameIdx);
    this.updateEyeBlink(nowMs);
    this.drawEyes(transition.headC, lay, faceAngle);
  }

  drawStarterCardOverlay(lay) {
    const card = this.assets.snake_card;
    const button = this.assets.play_button;
    if (!card || !button) {
      return;
    }
    this.ctx.fillStyle = `rgba(0, 0, 0, ${C.STARTER_CARD_DIM_ALPHA / 255})`;
    this.ctx.fillRect(0, 0, lay.winW, lay.winH);
    const gap = Math.max(8, C.STARTER_CARD_BUTTON_GAP);
    const blockH = card.height + gap + button.height;
    const centerTop = lay.boardOy + Math.max(0, Math.floor((lay.boardH - blockH) / 2));
    const blockTop = Math.max(lay.boardOy, centerTop - C.STARTER_CARD_Y_OFFSET);
    const cardRect = {
      x: Math.floor(lay.winW / 2 - card.width / 2),
      y: blockTop,
      w: card.width,
      h: card.height,
    };
    const buttonRect = {
      x: Math.floor(lay.winW / 2 - button.width / 2),
      y: cardRect.y + card.height + gap,
      w: button.width,
      h: button.height,
    };
    this.ctx.drawImage(card, cardRect.x, cardRect.y);
    this.ctx.drawImage(button, buttonRect.x, buttonRect.y);
    this.playButtonRect = buttonRect;
    const statY = cardRect.y + Math.round(card.height * C.STARTER_CARD_STAT_Y);
    const leftX = cardRect.x + Math.round(card.width * C.STARTER_CARD_STAT_LEFT_X);
    const rightX = cardRect.x + Math.round(card.width * C.STARTER_CARD_STAT_RIGHT_X);
    this.ctx.fillStyle = C.SCORE_COLOR;
    this.ctx.font = `bold ${Math.max(8, Math.floor(card.height * 0.10))}px Arial`;
    this.ctx.textBaseline = "middle";
    this.ctx.textAlign = "center";
    this.ctx.fillText(String(this.starterCardRunScore), leftX, statY);
    this.ctx.fillText(String(this.highScore), rightX, statY);
    this.ctx.textAlign = "left";
  }

  drawWaitingStartCue(lay) {
    const icon = this.assets.start_box;
    if (!icon) {
      return;
    }
    const pad = Math.max(8, C.WAITING_CUE_BOX_PAD);
    const boxW = icon.width + pad * 2;
    const boxH = icon.height + pad * 2;
    const boxX = lay.boardOx + Math.floor((lay.boardW - boxW) / 2);
    const boxY = lay.boardOy + Math.round(lay.boardH * C.WAITING_CUE_CENTER_Y_RATIO) - Math.floor(boxH / 2);
    this.drawRoundedRect(boxX, boxY, boxW, boxH, C.WAITING_CUE_BOX_RADIUS, `rgba(0,0,0,${C.WAITING_CUE_BOX_ALPHA / 255})`);
    this.ctx.drawImage(icon, boxX + Math.floor((boxW - icon.width) / 2), boxY + Math.floor((boxH - icon.height) / 2));
  }

  drawOverlay(lay) {
    if (this.starterCardVisible) {
      this.drawStarterCardOverlay(lay);
      return;
    }
    if (this.gameState === "waiting" && this.showWaitingStartCue) {
      this.drawWaitingStartCue(lay);
    }
  }

  drawWindowControls() {
    const fullIcon = this.maximized ? this.assets.not_full_screen : this.assets.full_screen;
    const volumeIcon = this.audioMuted ? this.assets.volume_muted : this.assets.volume;
    if (this.fsRect) {
      this.ctx.drawImage(fullIcon, this.fsRect.x, this.fsRect.y);
    }
    if (this.volRect) {
      this.ctx.drawImage(volumeIcon, this.volRect.x, this.volRect.y);
    }
  }

  draw(nowMs = this.now()) {
    if (!this.loaded) {
      this.drawBootFrame();
      return;
    }
    const lay = this.layout();
    const progress = this.headMotionProgress();
    this.playButtonRect = null;
    this.ctx.clearRect(0, 0, C.BASE_W, C.BASE_H);
    this.ctx.fillStyle = rgba(C.HEADER_COLOR);
    this.ctx.fillRect(0, 0, lay.winW, lay.headerH);
    this.drawHeader(lay);
    this.ctx.fillStyle = rgba(C.PANEL_COLOR);
    this.ctx.fillRect(0, lay.headerH, lay.winW, lay.winH - lay.headerH);
    this.drawTiles(lay);
    this.drawApple(lay, nowMs);
    this.drawSnake(lay, progress, nowMs);
    const [shakeX, shakeY] = this.collisionShakeOffsetPx(nowMs, lay);
    if (Math.abs(shakeX) > 0.01 || Math.abs(shakeY) > 0.01) {
      const gameplayLay = {
        ...lay,
        boardOx: lay.boardOx + Math.round(shakeX),
        boardOy: lay.boardOy + Math.round(shakeY),
      };
      this.ctx.save();
      this.ctx.beginPath();
      this.ctx.rect(lay.boardOx, lay.boardOy, lay.boardW, lay.boardH);
      this.ctx.clip();
      this.drawTiles(gameplayLay);
      this.drawApple(gameplayLay, nowMs);
      this.drawSnake(gameplayLay, progress, nowMs);
      this.ctx.restore();
      const borderW = Math.max(1, Math.round(C.BOARD_BORDER_STROKE_BASE * lay.sc));
      this.ctx.save();
      this.ctx.strokeStyle = rgba(C.PANEL_COLOR);
      this.ctx.lineWidth = borderW;
      this.ctx.strokeRect(
        lay.boardOx - borderW,
        lay.boardOy - borderW,
        lay.boardW + borderW * 2,
        lay.boardH + borderW * 2,
      );
      this.ctx.restore();
    }
    this.drawOverlay(lay);
    this.drawWindowControls();
    this.updateCursor();
  }

  drawBootFrame() {
    this.ctx.save();
    this.ctx.clearRect(0, 0, C.BASE_W, C.BASE_H);
    this.ctx.fillStyle = rgba(C.HEADER_COLOR);
    this.ctx.fillRect(0, 0, C.BASE_W, C.HEADER_H);
    this.ctx.fillStyle = rgba(C.PANEL_COLOR);
    this.ctx.fillRect(0, C.HEADER_H, C.BASE_W, C.BASE_H - C.HEADER_H);
    this.ctx.restore();
  }
}

window.snakeWeb = new SnakeWeb();
