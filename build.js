const esbuild = require('esbuild');
const path = require('path');

const buildOptions = {
  entryPoints: ['src/ui/main.ts'],
  bundle: true,
  outfile: 'src/ui/dist/bundle.js',
  format: 'iife',
  target: 'es2020',
  minify: process.env.NODE_ENV === 'production',
  sourcemap: process.env.NODE_ENV !== 'production',
  globalName: 'ChatApp',
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development')
  },
  loader: {
    '.ts': 'ts',
  },
  tsconfig: 'tsconfig.json'
};

// Build function
async function build() {
  try {
    await esbuild.build(buildOptions);
    console.log('✅ Build completed successfully');
  } catch (error) {
    console.error('❌ Build failed:', error);
    process.exit(1);
  }
}

// Watch function
async function watch() {
  try {
    const ctx = await esbuild.context(buildOptions);
    await ctx.watch();
    console.log('👀 Watching for changes...');
  } catch (error) {
    console.error('❌ Watch failed:', error);
    process.exit(1);
  }
}

// Export for programmatic use
module.exports = { build, watch, buildOptions };

// CLI usage
if (require.main === module) {
  const command = process.argv[2];
  
  if (command === 'watch') {
    watch();
  } else {
    build();
  }
}
