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
    var priceCollectionJobKey = new JobKey("PriceCollectionJob");
    q.AddJob<PriceCollectionJob>(opts => opts.WithIdentity(priceCollectionJobKey));
    q.AddTrigger(opts => opts
        .ForJob(priceCollectionJobKey)
        .WithIdentity("PriceCollectionJob-trigger")
        .WithCronSchedule(builder.Configuration["Quartz:PriceCollectionCron"] ?? "0 0 */2 * * ?"));

    var dailyReportJobKey = new JobKey("DailyReportJob");
    q.AddJob<DailyReportJob>(opts => opts.WithIdentity(dailyReportJobKey));
    q.AddTrigger(opts => opts
        .ForJob(dailyReportJobKey)
        .WithIdentity("DailyReportJob-trigger")
        .WithCronSchedule(builder.Configuration["Quartz:DailyReportCron"] ?? "0 0 18 * * ?"));
});

builder.Services.AddQuartzHostedService(opts => opts.WaitForJobsToComplete = true);

var host = builder.Build();
host.Run();