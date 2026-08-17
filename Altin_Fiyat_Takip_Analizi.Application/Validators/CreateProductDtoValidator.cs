using FluentValidation;
using Altin_Fiyat_Takip_Analizi.Application.DTOs;

namespace Altin_Fiyat_Takip_Analizi.Application.Validators;

public class CreateProductDtoValidator : AbstractValidator<CreateProductDto>
{
    public CreateProductDtoValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Ürün adı boş olamaz.")
            .MaximumLength(200);

        RuleFor(x => x.Category)
            .NotEmpty().WithMessage("Kategori boş olamaz.")
            .MaximumLength(100);

        RuleFor(x => x.OurPrice)
            .GreaterThan(0).WithMessage("Fiyat 0'dan büyük olmalı.");

        RuleFor(x => x.Currency)
            .NotEmpty()
            .Length(3).WithMessage("Para birimi 3 karakter olmalı (ör. TRY).");
    }
}