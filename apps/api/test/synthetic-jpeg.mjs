import sharp from 'sharp';
export const syntheticJpeg = () =>
  sharp({ create: { width: 320, height: 180, channels: 3, background: '#2b7062' } })
    .jpeg()
    .toBuffer();
