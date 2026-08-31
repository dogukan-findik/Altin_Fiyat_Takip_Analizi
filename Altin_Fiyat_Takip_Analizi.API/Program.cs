
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Application.Mapping;
using Altin_Fiyat_Takip_Analizi.Application.Validators;
using Altin_Fiyat_Takip_Analizi.Infrastructure.Data;
using Altin_Fiyat_Takip_Analizi.Infrastructure.Repositories;
using FluentValidation;
using FluentValidation.AspNetCore;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using Serilog;
using System.Text;

// --- Serilog'u en ba�ta, host bootstrap olmadan �nce kur ---
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Debug()
    .MinimumLevel.Override("Microsoft", Serilog.Events.LogEventLevel.Information)
    .Enrich.FromLogContext()
    .WriteTo.Console()
    .WriteTo.File("logs/log-.txt", rollingInterval: RollingInterval.Day)
    .CreateLogger();

var builder = WebApplication.CreateBuilder(args);

builder.Host.UseSerilog();

// --- Controllers + FluentValidation ---
builder.Services.AddControllers();
builder.Services.AddFluentValidationAutoValidation();
builder.Services.AddValidatorsFromAssemblyContaining<CreateProductDtoValidator>();

// --- EF Core ---
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

// --- Repository + AutoMapper ---
builder.Services.AddScoped(typeof(IRepository<>), typeof(Repository<>));
builder.Services.AddAutoMapper(typeof(MappingProfile));

// --- Application servisleri ---
builder.Services.AddScoped<IProductService, Altin_Fiyat_Takip_Analizi.Application.Services.ProductService>();
builder.Services.AddScoped<IPriceComparisonService, Altin_Fiyat_Takip_Analizi.Application.Services.PriceComparisonService>();
builder.Services.AddScoped<IReportService, Altin_Fiyat_Takip_Analizi.Application.Services.ReportGeneratorService>();
builder.Services.AddScoped<IPriceAlertService, Altin_Fiyat_Takip_Analizi.Application.Services.PriceAlertService>();
builder.Services.AddScoped<IPriceHistoryService, Altin_Fiyat_Takip_Analizi.Application.Services.PriceHistoryService>();
builder.Services.AddScoped<IJwtService, Altin_Fiyat_Takip_Analizi.Infrastructure.Services.JwtService>();
builder.Services.AddScoped<IAuthService, Altin_Fiyat_Takip_Analizi.Application.Services.AuthService>();
builder.Services.AddScoped<ISellerService, Altin_Fiyat_Takip_Analizi.Application.Services.SellerService>();
builder.Services.AddScoped<ISellerProductService, Altin_Fiyat_Takip_Analizi.Application.Services.SellerProductService>();

// --- Kendi fiyat guncelleme servisi (her 5 dakikada bir sync_own_prices.py calistirir) ---
builder.Services.AddHostedService<Altin_Fiyat_Takip_Analizi.API.BackgroundServices.OwnPriceSyncBackgroundService>();

// --- Pazaryeri canli tarama ve otomatik fiyat guncelleme servisi ---
builder.Services.AddSingleton<IScraperRunnerService, Altin_Fiyat_Takip_Analizi.Infrastructure.Services.ScraperRunnerService>();
builder.Services.AddHostedService<Altin_Fiyat_Takip_Analizi.API.BackgroundServices.MarketplacePriceSyncBackgroundService>();

// --- JWT Auth ---
var jwtKey = builder.Configuration["Jwt:Key"]
    ?? throw new InvalidOperationException("Jwt:Key appsettings.json'da tan�ml� de�il.");

builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = builder.Configuration["Jwt:Issuer"],
            ValidAudience = builder.Configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey))
        };
    });

builder.Services.AddAuthorization();

// --- Swagger (JWT destekli) ---
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "Altin Fiyat Takip Analizi API", Version = "v1" });

    c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Description = "JWT Authorization header. �rnek: \"Bearer {token}\"",
        Name = "Authorization",
        In = ParameterLocation.Header,
        Type = SecuritySchemeType.ApiKey,
        Scheme = "Bearer"
    });

    c.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference { Type = ReferenceType.SecurityScheme, Id = "Bearer" }
            },
            Array.Empty<string>()
        }
    });
});

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseMiddleware<Altin_Fiyat_Takip_Analizi.API.Middleware.ExceptionMiddleware>();

app.UseHttpsRedirection();
app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.Run();
