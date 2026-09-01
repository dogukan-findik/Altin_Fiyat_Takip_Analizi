using Altin_Fiyat_Takip_Analizi.Infrastructure.Data;
using Altin_Fiyat_Takip_Analizi.Infrastructure.Repositories;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Application.Mapping;
using Altin_Fiyat_Takip_Analizi.Scheduler.Jobs;
using Microsoft.EntityFrameworkCore;
using Quartz;

var builder = Host.CreateApplicationBuilder(args);

builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

builder.Services.AddScoped(typeof(IRepository<>), typeof(Repository<>));
builder.Services.AddAutoMapper(typeof(MappingProfile));

builder.Services.AddScoped<IReportService, Altin_Fiyat_Takip_Analizi.Application.Services.ReportGeneratorService>();
builder.Services.AddScoped<IPriceComparisonService, Altin_Fiyat_Takip_Analizi.Application.Services.PriceComparisonService>();

builder.Services.AddQuartz(q =>
{
    // 1) Rakip fiyat toplama — her 2 saatte bir
    var priceCollectionJobKey = new JobKey("PriceCollectionJob");
    q.AddJob<PriceCollectionJob>(opts => opts.WithIdentity(priceCollectionJobKey));
    q.AddTrigger(opts => opts
        .ForJob(priceCollectionJobKey)
        .WithIdentity("PriceCollectionJob-trigger")
        .WithCronSchedule(builder.Configuration["Quartz:PriceCollectionCron"] ?? "0 0 */2 * * ?"));

    // 2) Günlük rapor üretimi — her gün 18:00'de
    var dailyReportJobKey = new JobKey("DailyReportJob");
    q.AddJob<DailyReportJob>(opts => opts.WithIdentity(dailyReportJobKey));
    q.AddTrigger(opts => opts
        .ForJob(dailyReportJobKey)
        .WithIdentity("DailyReportJob-trigger")
        .WithCronSchedule(builder.Configuration["Quartz:DailyReportCron"] ?? "0 0 18 * * ?"));

    // 3) Ahlatcı kendi mağaza fiyatı güncelleme (sync_own_prices) — her 1 dakikada bir
    var ownPriceSyncJobKey = new JobKey("OwnPriceSyncJob");
    q.AddJob<OwnPriceSyncJob>(opts => opts.WithIdentity(ownPriceSyncJobKey));
    q.AddTrigger(opts => opts
        .ForJob(ownPriceSyncJobKey)
        .WithIdentity("OwnPriceSyncJob-trigger")
        .WithCronSchedule(builder.Configuration["Quartz:OwnPriceSyncCron"] ?? "0 */1 * * * ?"));

    var bankJobKey = new JobKey("BankPriceCollectionJob");
    q.AddJob<BankPriceCollectionJob>(opts => opts.WithIdentity(bankJobKey));
    q.AddTrigger(opts => opts
        .ForJob(bankJobKey)
        .WithIdentity("BankPriceCollectionJob-trigger")
        .WithCronSchedule(builder.Configuration["Quartz:BankPriceCollectionCron"] ?? "0 */5 * * * ?"));
});

builder.Services.AddQuartzHostedService(opts => opts.WaitForJobsToComplete = true);

var host = builder.Build();
host.Run();