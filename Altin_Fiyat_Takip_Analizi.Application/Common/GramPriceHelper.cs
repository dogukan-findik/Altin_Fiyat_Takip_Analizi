using System.Globalization;
using System.Text.RegularExpressions;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;

namespace Altin_Fiyat_Takip_Analizi.Application.Common;

public static class GramPriceHelper
{
    private static readonly Regex GramGoldNameRegex = new(
        @"^(?<gram>\d+(?:[.,]\d+)?)\s*Gram Alt[ıi]n$",
        RegexOptions.IgnoreCase | RegexOptions.CultureInvariant | RegexOptions.Compiled);

    public static decimal? TryParseGramGoldWeight(string productName)
    {
        if (string.IsNullOrWhiteSpace(productName))
            return null;

        var match = GramGoldNameRegex.Match(productName.Trim());
        if (!match.Success)
            return null;

        var raw = match.Groups["gram"].Value.Replace(',', '.');
        if (!decimal.TryParse(raw, NumberStyles.Number, CultureInfo.InvariantCulture, out var gram))
            return null;

        return gram > 0 ? gram : null;
    }

    public static decimal ResolveOurPrice(
        Product product,
        decimal storedPrice,
        IEnumerable<Product> allProducts,
        Func<int, decimal?> ownPriceByProductId)
    {
        if (storedPrice > 0)
            return storedPrice;

        var gram = TryParseGramGoldWeight(product.Name);
        if (gram is null)
            return storedPrice;

        foreach (var unitName in new[] { "1 Gram Altın", "Gram Altın" })
        {
            var unit = allProducts.FirstOrDefault(p =>
                p.IsActive && string.Equals(p.Name, unitName, StringComparison.OrdinalIgnoreCase));
            if (unit is null)
                continue;

            var unitPrice = ownPriceByProductId(unit.Id) ?? unit.OurPrice;
            if (unitPrice > 0)
                return Math.Round(unitPrice * gram.Value, 2);
        }

        foreach (var other in allProducts.Where(p => p.IsActive))
        {
            var otherGram = TryParseGramGoldWeight(other.Name);
            if (otherGram is null || otherGram == gram)
                continue;

            var otherPrice = ownPriceByProductId(other.Id) ?? other.OurPrice;
            if (otherPrice <= 0)
                continue;

            var unitPrice = otherPrice / otherGram.Value;
            if (unitPrice > 0)
                return Math.Round(unitPrice * gram.Value, 2);
        }

        return storedPrice;
    }
}
