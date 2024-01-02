const path = require('path');
const puppeteer = require('puppeteer');
const fs = require('fs/promises');

const MAX_RETRIES = 1;
const failedFile = 'failed_Screenshots.txt';
let failedScreenshots = [];

(async () => {
  // Delete the old log file if it exists
  try {
    await fs.unlink(failedFile);
    console.log(`Previous log file (${failedFile}) deleted.`);
  } catch (error) {
    console.log(`No previous log file found (${failedFile}). Proceeding...`);
  }

  const puppeteerOptions = {
    headless: true,
    timeout: 3000,
  };

  const browser = await puppeteer.launch(puppeteerOptions);

  try {
    const jsonData = await fs.readFile('live2d_models.json', 'utf8');
    const live2dModels = JSON.parse(jsonData);

    const overwriteImages = process.argv.includes('--overwrite');

    for (const model of live2dModels) {
      const { number, folder_name, file_path } = model;
      
      const normalizedPath = path.normalize(file_path);
      const parts = normalizedPath.split(path.sep);
      const finalPath = parts.slice(2).join(path.sep);
      const fullPath = path.join(__dirname, '..', finalPath);
      const fileName2 = path.basename(fullPath);
      const folderPath = path.dirname(fullPath);
      const fileName = `${folder_name}_thumbnail.png`;
      const filePath = path.join(folderPath, fileName);

      if (!overwriteImages) {
        try {
          await fs.access(filePath);
          console.log(`Thumbnail for model ${number} already exists. Skipping...`);
          continue;
        } catch (err) {
          // File doesn't exist, proceed with page load and screenshot
        }
      }
      let retries = 0;
      let success = false;
      while (retries <= MAX_RETRIES && !success) {
        const page = await browser.newPage();
        try {
          if (retries === 0) {
            await page.goto(`http://localhost:8000/Gallery/detail.html?modelNumber=${number}`, { waitUntil: 'networkidle0', timeout: 8000 });
          } else {
            await page.goto(`http://localhost:8000/Gallery/detail.html?modelNumber=${number}`, { timeout: 8000 });
            await page.waitForTimeout(3000); // Adding a 3-second delay before taking a screenshot on retry
          }

          await fs.mkdir(folderPath, { recursive: true });
          await page.waitForTimeout(3000); // Adding a 3-second delay before taking a screenshot on retry
          await page.screenshot({ path: filePath });
          console.log(`Thumbnail saved for model ${number} as ${filePath}`);

          await page.close();
          success = true;
        } catch (error) {
          console.error(`Error occurred for model ${number}:`, error);
          await page.close();
          retries++;
          if (retries <= MAX_RETRIES) {
            console.log(`Retrying for model ${number}...`);
            if (!failedScreenshots.includes(folderPath)) {
              failedScreenshots.push(folderPath);
              await fs.appendFile(failedFile, `${folderPath}\n`);
            }
          } else {
            console.log(`Max retries reached for model ${number}. Adding to failed list.`);
            if (!failedScreenshots.includes(folderPath)) {
              failedScreenshots.push(folderPath);
              await fs.appendFile(failedFile, `${folderPath}\n`);
            }
          }
        }
      }
    }
  } catch (error) {
    console.error('Error occurred:', error);
  } finally {
    await browser.close();
  }
})();