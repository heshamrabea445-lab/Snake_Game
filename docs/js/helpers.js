(() => {
  const shared = window.SnakeGameShared || (window.SnakeGameShared = {});

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function lerpPt(a, b, t) {
    return [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];
  }

  function smoothstep(t) {
    const clamped = Math.max(0, Math.min(1, t));
    return clamped * clamped * (3 - 2 * clamped);
  }

  function easeOutQuad(t) {
    const clamped = Math.max(0, Math.min(1, t));
    return 1 - (1 - clamped) * (1 - clamped);
  }

  function angleLerpShortest(a, b, t) {
    const diff = ((b - a + 180) % 360 + 360) % 360 - 180;
    return a + diff * t;
  }

  function mixColor(c1, c2, t) {
    return [
      Math.round(lerp(c1[0], c2[0], t)),
      Math.round(lerp(c1[1], c2[1], t)),
      Math.round(lerp(c1[2], c2[2], t)),
    ];
  }

  function rgba(parts, alpha = 1) {
    const [r, g, b] = parts;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  function triangleSample(min, max, mode) {
    const u = Math.random();
    const f = (mode - min) / (max - min);
    if (u < f) {
      return min + Math.sqrt(u * (max - min) * (mode - min));
    }
    return max - Math.sqrt((1 - u) * (max - min) * (max - mode));
  }

  function vecLen(x, y) {
    return Math.hypot(x, y);
  }

  function createCanvas(width, height) {
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(width));
    canvas.height = Math.max(1, Math.round(height));
    return canvas;
  }

  function copySubImage(image, rect) {
    const [sx, sy, sw, sh] = rect;
    const canvas = createCanvas(sw, sh);
    const ctx = canvas.getContext("2d");
    ctx.drawImage(image, sx, sy, sw, sh, 0, 0, sw, sh);
    return canvas;
  }

  function scaleCanvas(source, scale) {
    const canvas = createCanvas(source.width * scale, source.height * scale);
    const ctx = canvas.getContext("2d");
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(source, 0, 0, canvas.width, canvas.height);
    return canvas;
  }

  function scaleCanvasFitWidth(source, targetWidth) {
    const width = Math.max(1, Math.round(targetWidth));
    const height = Math.max(1, Math.round(source.height * width / source.width));
    const canvas = createCanvas(width, height);
    const ctx = canvas.getContext("2d");
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(source, 0, 0, width, height);
    return canvas;
  }

  function rotatePoint(cx, cy, px, py, angleDeg) {
    const rad = angleDeg * Math.PI / 180;
    const s = Math.sin(rad);
    const c = Math.cos(rad);
    const x = px - cx;
    const y = py - cy;
    return [cx + x * c - y * s, cy + x * s + y * c];
  }

  function drawCapsule(ctx, fillStyle, c1, c2, radius) {
    const dx = c2[0] - c1[0];
    const dy = c2[1] - c1[1];
    const dist = Math.hypot(dx, dy);
    ctx.fillStyle = fillStyle;
    if (dist < 0.5) {
      ctx.beginPath();
      ctx.arc(c1[0], c1[1], radius, 0, Math.PI * 2);
      ctx.fill();
      return;
    }
    const nx = -dy / dist * radius;
    const ny = dx / dist * radius;
    ctx.beginPath();
    ctx.moveTo(c1[0] + nx, c1[1] + ny);
    ctx.lineTo(c1[0] - nx, c1[1] - ny);
    ctx.lineTo(c2[0] - nx, c2[1] - ny);
    ctx.lineTo(c2[0] + nx, c2[1] + ny);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath();
    ctx.arc(c1[0], c1[1], radius, 0, Math.PI * 2);
    ctx.arc(c2[0], c2[1], radius, 0, Math.PI * 2);
    ctx.fill();
  }

  Object.assign(shared, {
    angleLerpShortest,
    copySubImage,
    createCanvas,
    drawCapsule,
    easeOutQuad,
    lerp,
    lerpPt,
    mixColor,
    rgba,
    rotatePoint,
    scaleCanvas,
    scaleCanvasFitWidth,
    smoothstep,
    triangleSample,
    vecLen,
  });
})();
