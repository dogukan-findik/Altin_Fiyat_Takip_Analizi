using System.Diagnostics;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using System.IO;
using Quartz;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;
using Altin_Fiyat_Takip_Analizi.Domain.Enums;

namespace Altin_Fiyat_Takip_Analizi.Scheduler.Jobs;

public class PriceCollectionJob : IJob
{
    private readonly IRepository<CollectionJob> _jobRepo;
    private readonly IConfiguration _configuration;
    private readonly ILogger<PriceCollectionJob> _logger;

    public PriceCollectionJob(
        IRepository<CollectionJob> jobRepo,
        IConfiguration configuration,
        ILogger<PriceCollectionJob> logger)
    {
        _jobRepo = jobRepo;
        _configuration = configuration;
        _logger = logger;
    }

    public async Task Execute(IJobExecutionContext context)
    {
        var job = new CollectionJob
        {
            JobType = "Scheduled",
            Status = JobStatus.Running,
            StartedAt = DateTime.UtcNow,
            TriggeredBy = "System"
        };
        await _jobRepo.AddAsync(job);
        await _jobRepo.SaveChangesAsync();
        var jobId = job.Id;

        var pythonPath = _configuration["Scraper:PythonPath"] ?? "python";
        var workingDirectory = _configuration["Scraper:WorkingDirectory"]
            ?? throw new InvalidOperationException("Scraper:ScraperScriptPath appsettings.json'da tanımlı değil.");

        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = pythonPath, // Doğrudan python.exe'ye gider
                Arguments = $"-m scraper.main --job-id {jobId}",
                WorkingDirectory = workingDirectory,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            _logger.LogInformation("Scraper başlatılıyor: {Python} -m scraper.main --job-id {JobId} (WorkingDirectory: {Dir})",
                pythonPath, jobId, workingDirectory);
            _logger.LogInformation("WorkingDirectory var mı: {Exists}", Directory.Exists(workingDirectory));

            using var process = Process.Start(psi)
                ?? throw new InvalidOperationException("Scraper process başlatılamadı.");

            var timeoutMs = int.Parse(_configuration["Scraper:TimeoutSeconds"] ?? "300") * 1000;
            var completed = process.WaitForExit(timeoutMs);

            var output = await process.StandardOutput.ReadToEndAsync();
            var error = await process.StandardError.ReadToEndAsync();

            if (!completed)
            {
                process.Kill();
                throw new TimeoutException("Scraper zaman aşımına uğradı.");
            }

            if (process.ExitCode != 0)
                throw new InvalidOperationException($"Scraper hata ile sonlandı (kod {process.ExitCode}): {error}");

            _logger.LogInformation("Scraper tamamlandı (JobId={JobId}). Çıktı: {Output}", jobId, output);
        }
        catch (Exception ex)
        {
            job.Status = JobStatus.Failed;
            job.CompletedAt = DateTime.UtcNow;
            job.ErrorMessage = ex.Message;
            _jobRepo.Update(job);
            await _jobRepo.SaveChangesAsync();
            _logger.LogError(ex, "PriceCollectionJob hata ile sonlandı (JobId={JobId}).", jobId);
        }
    }
}