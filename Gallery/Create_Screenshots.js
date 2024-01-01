const path = require('path');
const puppeteer = require('puppeteer');
const fs = require('fs/promises');

(async () => {
  const puppeteerOptions = {
    headless: true,
    timeout: 3000, // Setting the timeout to 8 seconds
  };

  const browser = await puppeteer.launch(puppeteerOptions);

  try {
    const jsonData = await fs.readFile('live2d_models.json', 'utf8');
    const live2dModels = JSON.parse(jsonData);

    for (const model of live2dModels) {
      const { number, folder_name, file_path } = model;

      const normalizedPath = path.normalize(file_path);
      const parts = normalizedPath.split(path.sep);
      const finalPath = parts.slice(2).join(path.sep);
      const fullPath = path.join(__dirname, '..', finalPath);
      const folderPath = path.dirname(fullPath);
      const fileName = `${folder_name}_thumbnail.png`;
      const filePath = path.join(folderPath, fileName);

      // Check if the file already exists
      try {
        await fs.access(filePath);
        console.log(`Thumbnail for model ${number} already exists. Skipping...`);
        continue; // Skip loading the page if the file already exists
      } catch (err) {
        // File doesn't exist, proceed with page load and screenshot
      }

      const page = await browser.newPage();
      try {
        await page.goto(`http://localhost:8000/Gallery/index.html?modelNumber=${number}`, { waitUntil: 'networkidle0', timeout: 8000 });

        await fs.mkdir(folderPath, { recursive: true });
        await page.screenshot({ path: filePath });
        console.log(`Thumbnail saved for model ${number} as ${filePath}`);

        await page.close();
      } catch (error) {
        console.error(`Error occurred for model ${number}:`, error);
        await page.close();
        continue; // Continue to the next model in case of errors
      }
    }
  } catch (error) {
    console.error('Error occurred:', error);
  } finally {
    await browser.close();
  }
})();
