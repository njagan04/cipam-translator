export const translateText = async (text, language) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(`Translated to ${language}: ${text}`);
    }, 1000);
  });
};
