// ̀-ͯ = Unicode combining diacritics block (NFD decomposition)
export function slugify(text: string, fallback = "proyecto"): string {
  return (
    text
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "")
      .substring(0, 50) || fallback
  );
}
