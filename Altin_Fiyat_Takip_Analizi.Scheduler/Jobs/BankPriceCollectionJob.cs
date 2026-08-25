using System.Diagnostics;
using Quartz;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;
using Altin_Fiyat_Takip_Analizi.Domain.Enums;

namespace Altin_Fiyat_Takip_Analizi.Scheduler.Jobs;

public class BankPriceCollectionJob : IJob
{
    private readonly IRepository<CollectionJob> _jobRepo;
    private readonly IConfiguration _configuration;
    private readonly ILogger<BankPriceCollectionJob> _logger;

    public BankPriceCollectionJob(
        IRepository<CollectionJob> jobRepo,
        IConfiguration configuration,
        ILogger<BankPriceCollectionJob> logger)
    {
        _jobRepo = jobRepo;
        _configuration = configuration;
        _logger = logger;
    }

    public async Task Execute(IJobExecutionContext context)
    {
        var job = new CollectionJob
        {
            JobType = "Scheduled-Bank",
            Status = JobStatus.Running,
            StartedAt = DateTime.UtcNow,
            TriggeredBy = "System"
        };
        await _jobRepo.AddAsync(job);
        await _jobRepo.SaveChangesAsync();
        var jobId = job.Id;

        var pythonPath = _configuration["Scraper:PythonPath"] ?? "python";
        var workingDirectory = _configuration["Scraper:WorkingDirectory"]
            ?? throw new InvalidOperationException("Scraper:WorkingDirectory appsettings.json'da tanımlı değil.");

        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = pythonPath,
                Arguments = $"-m scraper.sync_banks --job-id {jobId}",
                WorkingDirectory = workingDirectory,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            _logger.LogInformation("Banka scraper başlatılıyor: {Python} -m scraper.sync_banks --job-id {JobId}",
                pythonPath, jobId);

            using var process = Process.Start(psi)
                ?? throw new InvalidOperationException("Banka scraper process başlatılamadı.");

            var timeoutMs = int.Parse(_configuration["Scraper:BankTimeoutSeconds"] ?? "120") * 1000;
            var completed = process.WaitForExit(timeoutMs);

            var output = await process.StandardOutput.ReadToEndAsync();
            var error = await process.StandardError.ReadToEndAsync();

            if (!completed)
            {
                process.Kill();
                throw new TimeoutException("Banka scraper zaman aşımına uğradı.");
            }

            if (process.ExitCode != 0)
                throw new InvalidOperationException($"Banka scraper hata ile sonlandı (kod {process.ExitCode}): {error}");

            _logger.LogInformation("Banka scraper tamamlandı (JobId={JobId}). Çıktı: {Output}", jobId, output);
        }
        catch (Exception ex)
        {
            job.Status = JobStatus.Failed;
            job.CompletedAt = DateTime.UtcNow;
            job.ErrorMessage = ex.Message;
            _jobRepo.Update(job);
            await _jobRepo.SaveChangesAsync();
            _logger.LogError(ex, "BankPriceCollectionJob hata ile sonlandı (JobId={JobId}).", jobId);
        }
    }
}