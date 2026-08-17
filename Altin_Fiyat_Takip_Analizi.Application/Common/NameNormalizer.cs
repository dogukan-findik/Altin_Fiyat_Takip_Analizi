using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace Altin_Fiyat_Takip_Analizi.Application.Common;

 public static class NameNormalizer
{
    // '10Gr Gram Altın 22 Ayar' -> '10gr_gram_altin_22_ayar'
    public static string Normalize(string name)
    {
        var lower = name.ToLower(new CultureInfo("tr-TR"));
        var normalized = RemoveDiacritics(lower);

        // Gramaj standardizasyonu: "10gr", "10 gr", "10gram" -> "10gr"
        normalized = Regex.Replace(normalized, @"(\d+)\s*(gr|gram|g)\b", "$1gr");
        normalized = Regex.Replace(normalized, @"[^a-z0-9\s]", "");
        normalized = Regex.Replace(normalized.Trim(), @"\s+", "_");

        return normalized;
    }

    // 0-100 arası benzerlik skoru (Levenshtein tabanlı, Python'daki
    // SequenceMatcher.ratio() ile aynı amaca hizmet eder)
    public static decimal CalculateSimilarity(string name1, string name2)
    {
        var a = Normalize(name1);
        var b = Normalize(name2);

        if (a == b) return 100m;
        if (a.Length == 0 || b.Length == 0) return 0m;

        var distance = LevenshteinDistance(a, b);
        var maxLen = Math.Max(a.Length, b.Length);
        var ratio = 1 - (decimal)distance / maxLen;

        return Math.Round(ratio * 100, 2);
    }

    private static string RemoveDiacritics(string text)
    {
        var normalized = text.Normalize(NormalizationForm.FormD);
        var sb = new StringBuilder();
        foreach (var c in normalized)
        {
            var category = CharUnicodeInfo.GetUnicodeCategory(c);
            if (category != UnicodeCategory.NonSpacingMark)
                sb.Append(c);
        }
        return sb.ToString().Normalize(NormalizationForm.FormC);
    }

    private static int LevenshteinDistance(string a, string b)
    {
        var dp = new int[a.Length + 1, b.Length + 1];

        for (int i = 0; i <= a.Length; i++) dp[i, 0] = i;
        for (int j = 0; j <= b.Length; j++) dp[0, j] = j;

        for (int i = 1; i <= a.Length; i++)
        {
            for (int j = 1; j <= b.Length; j++)
            {
                var cost = a[i - 1] == b[j - 1] ? 0 : 1;
                dp[i, j] = Math.Min(
                    Math.Min(dp[i - 1, j] + 1, dp[i, j - 1] + 1),
                    dp[i - 1, j - 1] + cost);
            }
        }
        return dp[a.Length, b.Length];
    }
}



