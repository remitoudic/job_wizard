export function generateCoverLetterFilename(
	language: string,
	name: string,
	company: string,
	date: string
): string {
    let downloadName = `coverletter_${name}_${company}_${date}.pdf`;
    if (language === "french") {
        downloadName = `lettre_de_motivation_${name}_${company}_${date}.pdf`;
    } else if (language === "german") {
        downloadName = `anschreiben__${name}_${company}_${date}.pdf`;
    } else if (language === "spanish") {
        downloadName = `carta_de_presentacion_${name}_${company}_${date}.pdf`;
    }
    return downloadName;
}
