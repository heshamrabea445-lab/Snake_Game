(() => {
  const shared = window.SnakeGameShared || (window.SnakeGameShared = {});
  const {
    C,
    copySubImage,
    createCanvas,
    scaleCanvas,
    scaleCanvasFitWidth,
  } = shared;

  function loadImage(path) {
    return new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = reject;
      image.src = path;
    });
  }

  function makeAudio(path, volume, audioMuted) {
    const audio = new Audio(path);
    audio.preload = "auto";
    audio.volume = audioMuted ? 0 : volume;
    return { el: audio, baseVolume: volume };
  }

  function restoreUICanvases(game) {
    for (const [name, meta] of Object.entries(C.UI_CANVAS_METADATA)) {
      const source = game.raw[name];
      if (!source) {
        continue;
      }
      if (name === "start_box") {
        game.assets[name] = scaleCanvasFitWidth(source, C.WAITING_CUE_ICON_BASE_W);
        continue;
      }
      const [cw, ch] = meta.canvas;
      if (source.width === cw && source.height === ch) {
        game.assets[name] = source;
        continue;
      }
      const canvas = createCanvas(cw, ch);
      canvas.getContext("2d").drawImage(source, meta.offset[0], meta.offset[1]);
      game.assets[name] = canvas;
    }
    for (const name of ["tile_light", "tile_dark", "snake_card", "play_button", "volume", "volume_muted"]) {
      if (game.raw[name]) {
        game.assets[name] = game.raw[name];
      }
    }
  }

  function buildSpriteFrames(game) {
    game.assets.apple_board = scaleCanvasFitWidth(game.assets.apple_icon, C.TILE_SIZE);
    game.mouthFrames = C.MOUTH_RECTS.map((rect) => scaleCanvas(copySubImage(game.raw.mouth_strip, rect), C.MOUTH_SCALE));
    game.mouthFrameOpenAmounts = C.MOUTH_OPEN_AMOUNTS.slice();
    game.mouthPeakFrameIdx = game.mouthFrameOpenAmounts.reduce(
      (best, value, idx, arr) => value > arr[best] ? idx : best,
      0,
    );
    game.tongueFrames = C.TONGUE_RECTS.map((rect) => scaleCanvas(copySubImage(game.raw.tongue_strip, rect), C.TONGUE_SCALE));
    game.eyeFrames = [];
    const eyeFrameCount = 9;
    const eyeFrameWidth = 28;
    const eyeSep = 1;
    for (let i = 0; i < eyeFrameCount; i += 1) {
      const sx = i * (eyeFrameWidth + eyeSep);
      game.eyeFrames.push(scaleCanvas(
        copySubImage(game.raw.eye_strip, [sx, 0, eyeFrameWidth, game.raw.eye_strip.height]),
        C.EYE_SCALE,
      ));
    }
    game.deathFaceFrames = [];
    for (let i = 0; i < C.DEATH_FACE_FRAME_COUNT; i += 1) {
      const sx = i * (65 + 1);
      const frame = createCanvas(65, 58);
      const ctx = frame.getContext("2d");
      const [dx, dy] = C.DEATH_FACE_OFFSETS[i];
      ctx.drawImage(game.raw.death_strip, sx, 0, 65, 58, dx, dy, 65, 58);
      game.deathFaceFrames.push(scaleCanvas(frame, C.DEATH_FACE_SCALE));
    }
    game.collisionEffectFrames = [];
    const effectStrip = game.raw.collision_strip;
    for (let i = 0; i < C.COLLISION_EFFECT_FRAME_COUNT; i += 1) {
      const x0 = Math.round(i * effectStrip.width / C.COLLISION_EFFECT_FRAME_COUNT);
      const x1 = Math.round((i + 1) * effectStrip.width / C.COLLISION_EFFECT_FRAME_COUNT);
      const frame = copySubImage(effectStrip, [x0, 0, Math.max(1, x1 - x0), effectStrip.height]);
      game.collisionEffectFrames.push(scaleCanvas(frame, C.COLLISION_EFFECT_SCALE));
    }
  }

  async function loadAssets(game) {
    const imageDefs = {
      tile_light: "assets/images/light_green.png",
      tile_dark: "assets/images/dark_green.png",
      trophy: "assets/images/trophy.png",
      apple_icon: "assets/images/apple_icon.png",
      snake_card: "assets/images/Snake_card.png",
      play_button: "assets/images/play_button.png",
      start_box: "assets/images/start_box.png",
      full_screen: "assets/images/full_screen.png",
      not_full_screen: "assets/images/not_full_screen.png",
      volume: "assets/images/volume.png",
      volume_muted: "assets/images/muted.png",
      mouth_strip: "assets/sprites/mouth_sprite.png",
      tongue_strip: "assets/sprites/tongue_sprites.png",
      eye_strip: "assets/sprites/eye_sprite.png",
      death_strip: "assets/sprites/death_sprites.png",
      collision_strip: "assets/sprites/collision_effects_sprite.png",
    };
    const entries = await Promise.all(
      Object.entries(imageDefs).map(async ([key, path]) => [key, await loadImage(path)]),
    );
    game.raw = Object.fromEntries(entries);
    restoreUICanvases(game);
    buildSpriteFrames(game);
    game.audio.turn = makeAudio("assets/audio/turn_sfx.mp3", 0.35, game.audioMuted);
    game.audio.eat = makeAudio("assets/audio/eating.mp3", C.EAT_SFX_VOLUME, game.audioMuted);
    game.audio.collision = makeAudio("assets/audio/end_audio DEATH.mp3", 0.75, game.audioMuted);
  }

  Object.assign(shared, { loadAssets });
})();
