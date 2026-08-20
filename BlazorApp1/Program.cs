using Altin_Fiyat_Takip_Analizi.Web.Components;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddHttpClient<Altin_Fiyat_Takip_Analizi.Web.Services.ApiService>(client =>
{
    client.BaseAddress = new Uri("https://localhost:7268/"); // API'nin gerçek portu neyse onu yaz
});

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();

app.UseStaticFiles();
app.UseAntiforgery();

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();
